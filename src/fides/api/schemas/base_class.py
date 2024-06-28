from typing import Any, Callable, List

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic_core import ValidationError
from pydantic_core import core_schema as cs


class NoValidationSchema(BaseModel):
    """
    A schema to be used for API documentation only, when validation is
    handled later in the request process, but we still want valid request
    schemas to show up in the docs.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], cs.CoreSchema]
    ) -> cs.CoreSchema:

        schema = handler(source_type)

        def val(v: Any, _: cs.ValidatorFunctionWrapHandler) -> Any:
            return v

        return cs.no_info_wrap_validator_function(
            val, schema, serialization=schema.get("serialization")
        )


class FidesSchema(BaseModel):
    """A base template for all other Fides Schemas to inherit from."""

    @classmethod
    def get_field_names(cls) -> List[str]:
        """Return a list of all field names specified on this schema."""
        return list(cls.schema().get("properties", {}).keys())

    model_config = ConfigDict(from_attributes=True)
