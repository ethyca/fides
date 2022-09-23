# Configure Data Masking

## What is data masking?

Data masking is the process of obfuscating data in client systems, so it is no longer recognizable as PII (personally
identifiable information).

For example, if a customer requests that your remove all information associated with their email,
`test@example.com`, you might choose to "mask" that email with a random string, `xgoi4301nkyi79fjfdopvyjc5lnbr9`, and
their associated address with another random string `2ab6jghdg37uhkaz3hpyavpss1dvg2`.

!!! Tip "Masking does not equal anonymization. Since records are not deleted, a masked dataset is pseudonymized in most cases, and may still be identifiable if the masking is reversible or easy to predict."

In Fides, your options to pseudonymize data are captured in "masking strategies". Fides supports a wide variety
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

## Using Fides as a masking service
To use Fides as a masking service, send a `PUT` request to the masking endpoint with the value(s) you'd like pseudonymized. This endpoint is also useful for viewing how different masking strategies work.

### Masking example

```json title="<code>PUT /masking/mask</code>"
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

```json title="<code>Response 200 OK</code>"
    {
        "plain": ["test@example.com"],
        "masked_value": ["idkeaotbrub346ycbmpo@masked.com"]
    }
```

The email has been replaced with a random string of 20 characters, while still preserving that the value is an email.

See the [masking values](../api/index.md#operations-tag-Masking) API on how to use Fides to as a masking service.

## Configuration
Erasure requests will mask data with the chosen masking strategy.

To configure a specific masking strategy to be used for a Policy, you will create an `erasure` rule
that captures that strategy for the Policy.

```json title="<code>PATCH /policy/policy_key/rule</code>"
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

## Supported masking strategies

### Null rewrite

Masks the input value with a null value.

`strategy`: `null_rewrite`

No config needed.

### String rewrite

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

### Random string rewrite

Masks the input value with a random string of a specified length.

`strategy`: `random_string_rewrite`

`configuration`:

- `length` (optional): `int` that specifies length of randomly generated string. Default = `30`
- `format_preservation` (optional): `Dict` with the following key/vals:
  - `suffix`: `str` that specifies suffix to append to masked value

### AES encrypt

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

Issue a GET request to [`/api/v1/masking/strategy`](../api/index.md#operations-Masking-list_masking_strategies_api_v1_masking_strategy_get) to preview the different masking
strategies available, along with their configuration options.

## Extensibility

Fides asking strategies are built on top of an abstract `MaskingStrategy` base class.

`MaskingStrategy` has five methods: `mask`, `secrets_required`, `get_configuration_model`, `get_description`, and `data_type_supported`. For more detail on these methods, visit the class in the Fides repository. 

The below example focuses on the implementation of `RandomStringRewriteMaskingStrategy`:

```python
import string
from typing import Optional
from secrets import choice

from fides.api.ops.schemas.masking.masking_configuration import RandomStringMaskingConfiguration, MaskingConfiguration
from fides.api.ops.schemas.masking.masking_strategy_description import MaskingStrategyDescription
from fides.api.ops.service.masking.strategy.format_preservation import FormatPreservation
from fides.api.ops.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.ops.service.masking.strategy.masking_strategy_factory import (
    MaskingStrategyFactory,
)

RANDOM_STRING_REWRITE_STRATEGY_NAME = "random_string_rewrite"

@MaskingStrategyFactory.register(RANDOM_STRING_REWRITE_STRATEGY_NAME)
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

Note the arguments to the __init__ method. There is a field configuration of type `RandomStringMaskingConfiguration`.
This is the configuration for the masking strategy. It is used to house the options specified by the client as well as
any defaults that should be applied in their absence. All configuration classes extend from the
`MaskingConfiguration` class.

### Integrate the masking strategy factory

In order to leverage an implemented masking strategy, the `MaskingStrategy` subclass must be registered with the `MaskingStrategyFactory`. To register a new `MaskingStrategy`, use the `register` decorator on the `MaskingStrategy` subclass definition, as shown in the above example.

The value passed as the argument to the decorator must be the registered name of the `MaskingStrategy` subclass. This is the same value defined by [callers](#using-fides-as-a-masking-service) in the `"masking_strategy"."strategy"` field.
