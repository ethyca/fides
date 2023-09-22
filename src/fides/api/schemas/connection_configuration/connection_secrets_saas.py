import abc
from typing import Any, Dict, List, Type

from fideslang.models import FidesDatasetReference
from pydantic import BaseModel, Extra, Field, PrivateAttr, create_model, root_validator
from pydantic.fields import FieldInfo
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ValidationError
from fides.api.models.datasetconfig import validate_dataset_reference
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)
from fides.api.schemas.saas.saas_config import SaaSConfig


class SaaSSchema(BaseModel, abc.ABC):
    """
    Abstract base schema for updating SaaS connection configuration secrets.
    Fields are added during runtime based on the connector_params and any
    external_references in the passed in saas_config"""

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
            if connector_param:
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
                        invalid_options = [
                            entry for entry in value if entry not in options
                        ]
                        if invalid_options:
                            raise ValueError(
                                f"[{', '.join(invalid_options)}] are not valid options, '{name}' must be a list of values from [{', '.join(options)}]"
                            )

        return values

    @classmethod
    def get_connector_param(cls, name: str) -> Dict[str, Any]:
        return cls.__private_attributes__.get("_connector_params").default.get(name)  # type: ignore

    @classmethod
    def external_references(cls) -> List[str]:
        return [
            name
            for name, property in cls.schema()["properties"].items()
            if "external_reference" in property and property["external_reference"]
        ]

    class Config:
        """
        Certain SaaS workflows need to save secrets that are not part of the schema,
        such as access and refresh tokens for OAuth2. So we allow extra fields
        """

        extra = Extra.ignore
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
                Field(
                    title=connector_param.label,
                    description=connector_param.description,
                    default=connector_param.default_value,
                    sensitive=connector_param.sensitive,
                )
                if connector_param.default_value
                else (
                    param_type,
                    FieldInfo(
                        title=connector_param.label,
                        description=connector_param.description,
                        sensitive=connector_param.sensitive,
                    ),
                )
            )
        if self.saas_config.external_references:
            for external_reference in self.saas_config.external_references:
                field_definitions[external_reference.name] = (
                    FidesDatasetReference,
                    FieldInfo(
                        title=external_reference.label,
                        description=external_reference.description,
                        external_reference=True,  # metadata added so we can identify these secret schema fields as external references
                    ),
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
            _external_references=PrivateAttr(
                [
                    external_reference.name
                    for external_reference in self.saas_config.external_references
                ]
                if self.saas_config.external_references
                else []
            ),
        )

        return model


def validate_saas_secrets_external_references(
    db: Session,
    schema: SaaSSchema,
    connection_secrets: ConnectionConfigSecretsSchema,
) -> None:
    external_references = schema.external_references()
    for external_reference in external_references:
        dataset_reference: FidesDatasetReference = getattr(
            connection_secrets, external_reference
        )
        if dataset_reference.direction == "to":
            raise ValidationError(
                "External references can only have a direction of 'from', found 'to'"
            )
        validate_dataset_reference(db, dataset_reference)
