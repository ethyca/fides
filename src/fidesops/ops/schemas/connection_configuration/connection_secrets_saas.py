import abc
from typing import Any, Dict, Type

from pydantic import BaseModel, Extra, PrivateAttr, create_model, root_validator

from fidesops.ops.schemas.saas.saas_config import SaaSConfig


class SaaSSchema(BaseModel, abc.ABC):
    """
    Abstract base schema for updating SaaS connection configuration secrets.
    Fields are added during runtime based on the connector_params in the
    passed in saas_config"""

    @root_validator
    @classmethod
    def required_components_supplied(  # type: ignore
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that the minimum required components have been supplied."""

        # check required components are present
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

        # check the types and values are consistent with the option and multivalue fields
        for name, value in values.items():
            connector_param = cls.get_connector_param(name)
            options = connector_param.get("options")
            multiselect = connector_param.get("multiselect")

            if options:
                if isinstance(value, str):
                    if value not in options:
                        raise ValueError(
                            f"'{name}' must be one of [{', '.join(options)}]"
                        )
                elif isinstance(value, list):
                    if not multiselect:
                        raise ValueError(
                            "f'{name}' must be a single value when multiselect is not enabled, not a list"
                        )
                    invalid_options = [entry for entry in value if entry not in options]
                    if invalid_options:
                        raise ValueError(
                            f"[{', '.join(invalid_options)}] are not valid options, '{name}' must be a list of values from [{', '.join(options)}]"
                        )

        return values

    @classmethod
    def get_connector_param(cls, name: str) -> Dict[str, Any]:
        return cls.__private_attributes__.get("_connector_params").default.get(name)  # type: ignore

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

    # Pydantic uses the shorthand of (type, ...) to denote a required field of the given type
    def get_saas_schema(self) -> Type[SaaSSchema]:
        """Returns the schema for the current configuration"""
        field_definitions: Dict[str, Any] = {}
        for connector_param in self.saas_config.connector_params:
            param_type = list if connector_param.multiselect else str
            field_definitions[connector_param.name] = (
                connector_param.default_value
                if connector_param.default_value
                else (param_type, ...)
            )
        SaaSSchema.__doc__ = f"{str(self.saas_config.type).capitalize()} secrets schema"  # Dynamically override the docstring to create a description

        # set the connector_params as a private attribute on the schema class
        # so they can be accessible in the 'required_components_supplied' validator
        model: Type[SaaSSchema] = create_model(
            f"{self.saas_config.type}_schema",
            **field_definitions,
            __base__=SaaSSchema,
            _connector_params=PrivateAttr(
                {
                    connector_param.name: {
                        "options": connector_param.options,
                        "multiselect": connector_param.multiselect,
                    }
                    for connector_param in self.saas_config.connector_params
                }
            ),
        )

        return model
