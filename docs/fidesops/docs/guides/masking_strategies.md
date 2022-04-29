# How-To: Configure Data Masking Strategies

In this section we'll cover:

- What is data masking?
- Why might you want to mask personally identifiable information rather than delete?
- How do you use fidesops as a masking service only?
- How do you configure masking strategies for your fidesops policies?
- What are the current supported masking strategies in fidesops?
- How do you create your own masking strategies?


## Data masking basics 

Data masking is the process of obfuscating data in client systems, so it is no longer recognizable as PII (personally 
identifiable information.)

For example, if a customer requests that your remove all information associated with their email,
`test@example.com`, you might choose to "mask" that email with a random string, `xgoi4301nkyi79fjfdopvyjc5lnbr9`, and 
their associated address with another random string `2ab6jghdg37uhkaz3hpyavpss1dvg2`.

It's important to remember that masking != anonymization. Since records are not deleted, a masked dataset is (at best)
pseudonymized in most cases, and (at worst) may still be identifiable if the masking is reversible or easy to predict,
which is a common mistake!

In fidesops, your options to pseudonymize data are captured in "masking strategies". Fidesops supports a wide variety
of masking strategies for different purposes when used directly as an API including HMAC, Hash, AES encryption, string rewrite, random string rewrite, and null rewrite.


### Why mask instead of delete?

Deleting customer data may involve entirely deleting a whole record (all attributes of the entity) or permanent and 
irreversible anonymization of the record by updating specific fields within a record with masked values.

Using a masking strategy instead of straight deletion to obscure PII helps ensure referential integrity in your 
database. For example, you might have an `orders` table with a foreign key to `user` without cascade delete. Say you first 
deleted a user with email `test@example.com` without addressing their orders, you could potentially 
have lingering orphans in the `orders` table. Using masking as a "soft delete" might be a safer strategy 
depending on how your tables are defined.

In order to ensure referential integrity is retained, any values that represent foreign keys must be consistently 
updated with the same masked values across all sources.

Other reasons to mask instead of delete include legal requirements that have you retain certain data for a certain length of time.


## Using fidesops as a masking service

If you just want to use fidesops as a masking service, you can send a `PUT` request to the masking endpoint with the 
value(s) you'd like pseudonymized. This endpoint is also useful for getting a feel of how the different masking strategies work.

Example: `PUT /masking/mask`

```json
     {
        "values": ["test@example.com"],
        "masking_strategy": {
            "strategy": "random_string_rewrite",
            "configuration": {
                "length": 20,
                "format_preservation": {
                    "suffix": "@masked.com"
                }
            }
        }
    }
```

`Response 200 OK`

```json
    {
        "plain": ["test@example.com"],
        "masked_value": ["idkeaotbrub346ycbmpo@masked.com"]
    }
```

The email has been replaced with a random string of 20 characters, while still preserving that the value is an email.

See [Masking values API docs](/fidesops/api#operations-tag-Masking) on how to use fidesops to as a masking service .


## Configuration

Erasure requests will mask data with the chosen masking strategy.

To configure a specific masking strategy to be used for a Policy, you will create an `erasure` rule
that captures that strategy for the Policy.

Issue a PATCH request to `/policy/policy_key/rule`:

```json
    [{
        "name": "Global erasure rule",
        "action_type": "erasure",
        "key": "string_rewrite_rule",
        "masking_strategy": {
            "strategy": "random_string_rewrite",
            "configuration": {
                "length": 20,
                "format_preservation": {
                    "suffix": "@masked.com"
                }   
            }
        }
    }]

```

## Supported Masking Strategies and Associated Configuration options

### Null Rewrite

Masks the input value with a null value.

`strategy`: `null_rewrite`

No config needed.

### String Rewrite

Masks the input value with a default string value.

`strategy`: `string_rewrite`

`configuration`:

- `rewrite_value`: `str` that will replace input values
- `format_preservation` (optional): `Dict` with the following key/vals:
    - `suffix`: `str` that specifies suffix to append to masked value

### Hash

Masks the data by hashing the input before returning it. The hash is deterministic such that the same input will return the same output within the context of the same privacy request. This is not the case when the masking service is called as a standalone service, outside the context of a privacy request.

`strategy`: `hash`

`configuration`:

- `algorithm` (optional): `str` that specifies Hash masking algorithm. Options include `SHA-512` or `SHA_256`. Default = `SHA_256`
- `format_preservation` (optional): `Dict` with the following key/vals:
    - `suffix`: `str` that specifies suffix to append to masked value

### Random String Rewrite

Masks the input value with a random string of a specified length.

`strategy`: `random_string_rewrite`

`configuration`:

- `length` (optional): `int` that specifies length of randomly generated string. Default = `30`
- `format_preservation` (optional): `Dict` with the following key/vals:
    - `suffix`: `str` that specifies suffix to append to masked value

### AES Encrypt

Masks the data using AES encryption before returning it. The AES encryption strategy is deterministic such that the same input will return the same output within the context of the same privacy request. This is not the case when the masking service is called as a standalone service, outside the context of a privacy request.

`strategy`: `aes_encrypt`

`configuration`:

- `mode` (optional): `str` that specifies AES encryption mode. Only supported option is `GCM`. Default = `GCM`
- `format_preservation` (optional): `Dict` with the following key/vals:
    - `suffix`: `str` that specifies suffix to append to masked value

### HMAC

Masks the data using HMAC before returning it. The HMAC encryption strategy is deterministic such that the same input will return the same output within the context of the same privacy request. This is not the case when the masking service is called as a standalone service, outside the context of a privacy request.

`strategy`: `hmac`

`configuration`:

- `algorithm` (optional): `str` that specifies HMAC masking algorithm. Options include `SHA-512` or `SHA_256`. Default = `SHA_256`
- `format_preservation` (optional): `Dict` with the following key/vals:
    - `suffix`: `str` that specifies suffix to append to masked value

    
See the [Policy guide](policies.md) for more detailed instructions on creating Policies and Rules.


## Getting masking options

Issue a GET request to [`/api/v1/masking/strategy`](/fidesops/api#operations-Masking-list_masking_strategies_api_v1_masking_strategy_get) to preview the different masking
strategies available, along with their configuration options. 


## Extensibility

In fidesops, masking strategies are all built on top of an abstract base class - `MaskingStrategy`. 
MaskingStrategy has five methods - `mask`, `secrets_required`,  `get_configuration_model`, `get_description`, and `data_type_supported`. For more detail on these 
methods, visit the class in the fidesops repository. For now, we will focus on the implementation of
`RandomStringRewriteMaskingStrategy` below:


```python
import string
from typing import Optional
from secrets import choice

from fidesops.schemas.masking.masking_configuration import RandomStringMaskingConfiguration, MaskingConfiguration
from fidesops.schemas.masking.masking_strategy_description import MaskingStrategyDescription
from fidesops.service.masking.strategy.format_preservation import FormatPreservation
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy


class RandomStringRewriteMaskingStrategy(MaskingStrategy):
    """Masks a value with a random string of the length specified in the configuration."""

    def __init__(
        self,
        configuration: RandomStringMaskingConfiguration,
    ):
        self.length = configuration.length
        self.format_preservation = configuration.format_preservation

    def mask(self, values: Optional[List[str]], privacy_request_id: Optional[str]) -> Optional[List[str]]:
        """Replaces the value with a random lowercase string of the configured length"""
        if values is None:
            return None
        masked_values: List[str] = []
        for _ in range(len(values)):
            masked: str = "".join(
                [
                    choice(string.ascii_lowercase + string.digits)
                    for _ in range(self.length)
                ]
            )
            if self.format_preservation is not None:
                formatter = FormatPreservation(self.format_preservation)
                masked = formatter.format(masked)
            masked_values.append(masked)
        return masked_values

    @staticmethod
    def get_configuration_model() -> MaskingConfiguration:
        """Not covered in this example"""

    @staticmethod
    def get_description() -> MaskingStrategyDescription:
        """Not covered in this example"""

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Not covered in this example"""
```

The `mask` method will be called with the list of values to be masked and the masked values will be the output. In this case, we want to replace the supplied values with a random mixture of ascii lowercase letters and digits of the 
specified length. If format preservation is specified, for example, we still want to know that an email was an email, 
we might tack on an email-like suffix.

Note the arguments to the __init__ method - there is a field configuration of type `RandomStringMaskingConfiguration`. 
This is the configuration for the masking strategy. It is used to house the options specified by the client as well as 
any defaults that should be applied in their absence. All configuration classes extend from the 
`MaskingConfiguration` class.

### Integrating with the Masking Strategy Factory

Now that we know how a masking strategy is built in the system and how a masking strategy is configured, we will cover 
how to enable the linkage between the two. In other words, how do we run the masking strategy that we have configured? 
The answer to that is the Masking Strategy Factory.

The masking strategy factory is defined in the `masking_strategy_factory.py` file. The pertinent sections have been 
pasted below:

```python
from enum import Enum
from typing import Dict, Union

from pydantic import ValidationError

from fidesops.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)
from fidesops.common_exceptions import ValidationError as FidesopsValidationError

from fidesops.schemas.masking.masking_configuration import FormatPreservationConfig

class SupportedMaskingStrategies(Enum):
    string_rewrite = StringRewriteMaskingStrategy
    hash = HashMaskingStrategy
    random_string_rewrite = RandomStringRewriteMaskingStrategy
    aes_encrypt = AesEncryptionMaskingStrategy
    hmac = HmacMaskingStrategy
    

def get_strategy(
    strategy_name: str,
    configuration: Dict[
        str,
        Union[str, FormatPreservationConfig],
    ],
) -> MaskingStrategy:
    """
    Returns the strategy given the name and configuration.
    Raises NoSuchStrategyException if the strategy does not exist
    """
    if strategy_name not in SupportedMaskingStrategies.__members__:
        valid_strategies = ", ".join([s.name for s in SupportedMaskingStrategies])
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )
    strategy = SupportedMaskingStrategies[strategy_name].value
    try:
        strategy_config = strategy.get_configuration_model()(**configuration)
        return strategy(configuration=strategy_config)
    except ValidationError as e:
        raise FidesopsValidationError(message=str(e))

```


The `SupportedMaskingStrategy` enum maps the strategy name to the masking strategy implementation class. 

After creating a new masking strategy and configuration, just register it in this enum, and it will be ready for use by the system.
