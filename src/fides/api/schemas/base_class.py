from typing import Any, Callable, List

from pydantic import BaseModel, ConfigDict
from pydantic_core import core_schema


class NoValidationSchema(BaseModel):
    """
    A schema to be used for API documentation only, when validation is
    handled later in the request process, but we still want valid request
    schemas to show up in the docs.
    """

    @classmethod
    def __get_pydantic_core_schema__(  # pylint: disable=arguments-differ
        cls, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        """Custom override for Pydantic V2 - allows us to defer validation for
        connection secrets schemas until later."""

        schema = handler(source_type)

        def val(v: Any, _: core_schema.ValidatorFunctionWrapHandler) -> Any:
            return v

        return core_schema.no_info_wrap_validator_function(
            function=val, schema=schema, serialization=schema.get("serialization")
        )


class FidesSchema(BaseModel):
    """A base template for all other Fides Schemas to inherit from."""

    @classmethod
    def get_field_names(cls) -> List[str]:
        """Return a list of all field names specified on this schema."""
        return list(cls.schema().get("properties", {}).keys())

    model_config = ConfigDict(from_attributes=True)
