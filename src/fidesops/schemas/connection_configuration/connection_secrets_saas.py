import abc
from typing import Any, Dict, Type

from pydantic import BaseModel, Extra, create_model, root_validator

from fidesops.schemas.saas.saas_config import SaaSConfig


class SaaSSchema(BaseModel, abc.ABC):
    """
    Abstract base schema for updating SaaS connection configuration secrets.
    Fields are added during runtime based on the connector_params in the
    passed in saas_config"""

    @root_validator
    @classmethod
    def required_components_supplied(  # type: ignore
        cls: BaseModel, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that the minimum required components have been supplied."""

        required_components = [
            name for name, attributes in cls.__fields__.items() if attributes.required
        ]
        min_fields_present = all(
            values.get(component) for component in required_components
        )
        if not min_fields_present:
            raise ValueError(
                f"{cls.__name__} must be supplied all of: [{', '.join(required_components)}]."  # type: ignore
            )

        return values

    class Config:
        """Only permit selected secret fields to be stored."""

        extra = Extra.forbid
        orm_mode = True


class SaaSSchemaFactory:
    """
    Takes the base SaaS schema which only contains a field validator
    and uses the saas_config to generate the schema for the specific connector
    """

    def __init__(self, saas_config: SaaSConfig):
        self.saas_config = saas_config

    # Pydantic uses the shorthand of (str, ...) to denote a required field of type str
    def get_saas_schema(self) -> Type[SaaSSchema]:
        """Returns the schema for the current configuration"""
        field_definitions: Dict[str, Any] = {}
        for connector_param in self.saas_config.connector_params:
            field_definitions[connector_param.name] = (
                connector_param.default_value
                if connector_param.default_value
                else (str, ...)
            )
        SaaSSchema.__doc__ = f"{str(self.saas_config.type).capitalize()} secrets schema"  # Dynamically override the docstring
        model: Type[SaaSSchema] = create_model(
            f"{self.saas_config.fides_key}_schema",
            **field_definitions,
            __base__=SaaSSchema,
        )

        return model
