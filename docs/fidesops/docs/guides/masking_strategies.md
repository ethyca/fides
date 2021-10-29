# How-To: Configure Data Masking Strategies

In this section we'll cover:

- What is a data masking?
- Why might you want to mask personally identifiable information rather than delete?
- What are the currently-supported masking strategies in fidesops?
- How do you configure masking strategies for your fidesops policies?
- How do you use fidesops as a masking service only?
- How do you create your own masking strategies?


## Data masking basics 

Data masking is the process of obfuscating data in client systems, so it is no longer recognizable as PII (personally 
identifiable information.)  

For example, if a customer requests that your remove all information associated with their email,
`test@example.com`, you might choose to "mask" that email with a random string, `xgoi4301nkyi79fjfdopvyjc5lnbr9`, and 
their associated address with another random string `2ab6jghdg37uhkaz3hpyavpss1dvg2`.

In FidesOps, your options to pseudonymize data are captured in masking strategies. 


### Why mask instead of delete?

Deleting customer data may involve entirely deleting a whole record (all attributes of the entity) or permanent and 
irreversible anonymization of the record by updating specific fields within a record with masked values.

Using a masking strategy instead of straight deletion to obscure PII helps ensure referential integrity in your 
database.  For example, you might have an `orders` table with a foreign key to `user` without cascade delete. Say you first 
deleted a user with email `test@example.com` without addressing their orders, you could potentially 
have a lot of lingering orphans in the `orders` table. Using masking as a "soft delete" might be a safer strategy 
depending on how your tables are defined.

In order to ensure referential integrity is retained, any values that represent foreign keys must be consistently 
updated with the same masked values across all sources.

Other reasons to mask instead of delete include legal requirements that have you retain certain data for a certain length of time.  


### Supported Strategies

  - `StringRewriteMaskingStrategy`: Masks the input value with a default string value
  - `HashMaskingStrategy`: Masks the input value by returning a hashed version of the input value
  - `RandomStringRewriteMaskingStrategy`: Masks the input value with a random string of a specified length
  - `AesEncryptionMaskingStrategy`: Masks by encrypting the value using AES
  - `HmacMaskingStrategy`: Masks the input value by using the HMAC algorithm along with a hashed version of the data and a secret key

## Configuration

This is still in progress.  Big picture, you'll create a Policy, then you'll create a Rule for that policy.  On the
Rule, you'll specify your masking strategy, and the config for that strategy.  

When a `delete` query is executed, it needs to respect the masking strategy on the rule.

TODO update docs when this is complete.

## Specifying Encryption Keys

- How do I specify the encryption key to use for AES or HMAC?
- Alternatively, can the key be an auto-generated, one-time use key that is discarded?

TODO update docs once this is complete.

## Using Fidesops as a masking service

Send a PUT request to the masking endpoint with the value as the text you'd like pseudonymized to see an example 
of how the masking strategy might obscure your data.

See [Masking values API docs](http://0.0.0.0:8080/docs#/Masking/mask_value_api_v1_masking_mask_put) on how to use fidesops to as a masking service 

You can also use this endpoint to test a specific masking strategy. 

### Example request

In this example, I want to mask email `test@example.com` with a random string of length 20, 
and tack on a `@masked.com` to preserve the format.

`PUT /api/v1/masking/mask?value=test@example.com`


```json
 {
    "strategy": "random_string_rewrite",
    "configuration": {
        "length": 20,
        "format_preservation": {
            "suffix": "@masked.com"
        }
        
    }
}
```
### Sample response

```json
{
    "plain": "test@example.com",
    "masked_value": "v59ch40i1el3p25xrchz@masked.com"
}

```

## Getting masking options

Issue a GET request to [`/api/v1/masking/strategy`](http://0.0.0.0:8080/docs#/Masking/list_masking_strategies_api_v1_masking_strategy_get) to preview the different masking
strategies available, along with their configuration options. 


## Extensibility

In Fidesops, masking strategies are all built on top of an abstract base class - `MaskingStrategy`. 
MaskingStrategy has three methods - `mask`, `get_configuration_model` and `get_description`. For more detail on these 
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

    def mask(self, value: Optional[str]) -> Optional[str]:
        """Replaces the value with a random lowercase string of the configured length"""
        if value is None:
            return None
        masked: str = "".join(
            [choice(string.ascii_lowercase + string.digits) for _ in range(self.length)]
        )
        if self.format_preservation is not None:
            formatter = FormatPreservation(self.format_preservation)
            return formatter.format(masked)
        return masked

    @staticmethod
    def get_configuration_model() -> MaskingConfiguration:
        """Not covered in this example"""

    @staticmethod
    def get_description() -> MaskingStrategyDescription:
        """Not covered in this example"""
```

The `mask` method will be called with the value to be masked and the masked value will be the output. In this case,
if a value is supplied, we want to replace it with a random mixture of ascii lowercase letters and digits of the 
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
from fidesops.common_exceptions import ValidationError as SolonValidationError

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
        raise SolonValidationError(message=str(e))

```


The `SupportedMaskingStrategy` enum maps the strategy name to the masking strategy implementation class. 

After creating a new masking strategy and configuration, just register it in this enum and it will be ready for use by the system.
