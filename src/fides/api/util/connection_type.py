from __future__ import annotations

from typing import Any, Set

from fides.api.common_exceptions import NoSuchConnectionTypeSecretSchemaError
from fides.api.models.connectionconfig import ConnectionType
from fides.api.schemas.connection_configuration import (
    SaaSSchemaFactory,
    secrets_schemas,
)
from fides.api.schemas.connection_configuration.connection_type_system_map import (
    ConnectionSystemTypeMap,
)
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.api.schemas.policy import SUPPORTED_ACTION_TYPES, ActionType
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.service.connectors.consent_email_connector import (
    CONSENT_EMAIL_CONNECTOR_TYPES,
)
from fides.api.service.connectors.erasure_email_connector import (
    ERASURE_EMAIL_CONNECTOR_TYPES,
)
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
)
from fides.api.util.saas_util import load_config_from_string


def transform_v2_to_v1_in_place(schema):
    """Connection secrets endpoint was previously returning the pydantic v1 schema, so
    with pydantic v2, trying to revert to the old schema since the FE is built off of it
    """

    def transform_any_of(field_attributes_mapping):
        for attributes in field_attributes_mapping.values():
            # Transforming Pydantic V2 schemas -> Pydantic V1 schemas
            if attributes.get("anyOf"):
                anyOf = attributes.get("anyOf")
                for type_annotation in anyOf:
                    if "type" in type_annotation and type_annotation["type"] != "null":
                        for key, val in type_annotation.items():
                            attributes[key] = val
                        break
                    if "$ref" in type_annotation:
                        ref = type_annotation["$ref"]
                        attributes["allOf"] = [
                            {"$ref": ref.replace("#/$defs", "#/definitions")}
                        ]
                        break

                attributes.pop("anyOf")

            if "default" in attributes and attributes["default"] is None:
                # Backwards compatible with UI
                attributes.pop("default")

            if attributes.get("$ref"):
                ref = attributes["$ref"]
                attributes["$ref"] = ref.replace("#/$defs", "#/definitions")

    transform_any_of(schema["properties"])

    for attributes in schema["properties"].values():
        if attributes.get("allOf"):
            for defs in attributes.get("allOf"):
                for key, val in defs.items():
                    defs[key] = val.replace("#/$defs", "#/definitions")

    if schema.get("$defs"):
        schema["definitions"] = schema.get("$defs")
        schema.pop("$defs")
        for key, definition in schema["definitions"].items():
            if definition.get("properties"):
                transform_any_of(definition["properties"])


def get_connection_type_secret_schema(*, connection_type: str) -> dict[str, Any]:
    """Returns the secret fields that should be supplied to authenticate with a particular connection type.

    Note that this does not return actual secrets, instead we return the *types* of
    secret fields needed to authenticate.
    """
    connection_system_types: list[ConnectionSystemTypeMap] = get_connection_types()
    if not any(item.identifier == connection_type for item in connection_system_types):
        raise NoSuchConnectionTypeSecretSchemaError(
            f"No connection type found with name '{connection_type}'."
        )

    if connection_type in [db_type.value for db_type in ConnectionType]:
        schema = secrets_schemas[connection_type].schema()
        transform_v2_to_v1_in_place(schema)
        return schema

    connector_template = ConnectorRegistry.get_connector_template(connection_type)
    if not connector_template:
        raise NoSuchConnectionTypeSecretSchemaError(
            f"No SaaS connector type found with name '{connection_type}'."
        )

    config = SaaSConfig(**load_config_from_string(connector_template.config))
    schema = SaaSSchemaFactory(config).get_saas_schema().schema()
    transform_v2_to_v1_in_place(schema)

    # rearrange the default order of the properties generated by Pydantic
    # to reflect the order defined in the connector_params and external_references
    order = [connector_param.name for connector_param in config.connector_params]
    if config.external_references:
        order.extend(
            [
                external_reference.name
                for external_reference in config.external_references
            ]
        )

    schema["properties"] = {
        name: value
        for name, value in sorted(
            schema["properties"].items(), key=lambda item: order.index(item[0])
        )
    }
    if schema.get("additionalProperties"):
        schema.pop("additionalProperties")
    return schema


def get_connection_types(
    search: str | None = None,
    system_type: SystemType | None = None,
    action_types: Set[ActionType] = SUPPORTED_ACTION_TYPES,
) -> list[ConnectionSystemTypeMap]:
    def is_match(elem: str) -> bool:
        """If a search query param was included, is it a substring of an available connector type?"""
        return search.lower() in elem.lower() if search else True

    def saas_request_type_filter(connection_type: str) -> bool:
        """
        If any of the request type filters are set to true,
        ensure the given saas connector supports requests of at least one of those types.
        """
        if SUPPORTED_ACTION_TYPES == action_types:
            # if none of our filters are enabled, pass quickly to avoid unnecessary overhead
            return True

        template = ConnectorRegistry.get_connector_template(connection_type)
        if template is None:  # shouldn't happen, but we can be safe
            return False

        # Check if the necessary actions are supported
        return any(
            action_type in template.supported_actions for action_type in action_types
        )

    connection_system_types: list[ConnectionSystemTypeMap] = []
    if (system_type == SystemType.database or system_type is None) and (
        ActionType.access in action_types or ActionType.erasure in action_types
    ):
        database_types: list[str] = sorted(
            [
                conn_type.value
                for conn_type in ConnectionType
                if conn_type
                not in [
                    ConnectionType.attentive,
                    ConnectionType.fides,
                    ConnectionType.generic_consent_email,
                    ConnectionType.generic_erasure_email,
                    ConnectionType.https,
                    ConnectionType.manual,
                    ConnectionType.manual_webhook,
                    ConnectionType.saas,
                    ConnectionType.sovrn,
                ]
                and is_match(conn_type.value)
            ]
        )
        connection_system_types.extend(
            [
                ConnectionSystemTypeMap(
                    identifier=item,
                    type=SystemType.database,
                    human_readable=ConnectionType(item).human_readable,
                    supported_actions=[ActionType.access, ActionType.erasure],
                )
                for item in database_types
            ]
        )
    if system_type == SystemType.saas or system_type is None:
        saas_types: list[str] = sorted(
            [
                saas_type
                for saas_type in ConnectorRegistry.connector_types()
                if is_match(saas_type) and saas_request_type_filter(saas_type)
            ]
        )

        for item in saas_types:
            connector_template = ConnectorRegistry.get_connector_template(item)
            if connector_template is not None:
                connection_system_types.append(
                    ConnectionSystemTypeMap(
                        identifier=item,
                        type=SystemType.saas,
                        human_readable=connector_template.human_readable,
                        encoded_icon=connector_template.icon,
                        authorization_required=connector_template.authorization_required,
                        user_guide=connector_template.user_guide,
                        supported_actions=connector_template.supported_actions,
                    )
                )

    if (system_type == SystemType.manual or system_type is None) and (
        ActionType.access in action_types or ActionType.erasure in action_types
    ):
        manual_types: list[str] = sorted(
            [
                manual_type.value
                for manual_type in ConnectionType
                if manual_type == ConnectionType.manual_webhook
                and is_match(manual_type.value)
            ]
        )
        connection_system_types.extend(
            [
                ConnectionSystemTypeMap(
                    identifier=item,
                    type=SystemType.manual,
                    human_readable=ConnectionType(item).human_readable,
                    supported_actions=[ActionType.access, ActionType.erasure],
                )
                for item in manual_types
            ]
        )

    if system_type == SystemType.email or system_type is None:
        email_types: list[str] = sorted(
            [
                email_type.value
                for email_type in ConnectionType
                if email_type
                in ERASURE_EMAIL_CONNECTOR_TYPES + CONSENT_EMAIL_CONNECTOR_TYPES
                and is_match(email_type.value)
                and (  # include consent or erasure connectors if requested, respectively
                    (
                        ActionType.consent in action_types
                        and email_type in CONSENT_EMAIL_CONNECTOR_TYPES
                    )
                    or (
                        ActionType.erasure in action_types
                        and email_type in ERASURE_EMAIL_CONNECTOR_TYPES
                    )
                )
            ]
        )
        connection_system_types.extend(
            [
                ConnectionSystemTypeMap(
                    identifier=email_type,
                    type=SystemType.email,
                    human_readable=ConnectionType(email_type).human_readable,
                    supported_actions=[
                        (
                            ActionType.consent
                            if ConnectionType(email_type)
                            in CONSENT_EMAIL_CONNECTOR_TYPES
                            else ActionType.erasure
                        )
                    ],
                )
                for email_type in email_types
            ]
        )
    return connection_system_types
