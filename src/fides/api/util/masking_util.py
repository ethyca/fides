from typing import Any, Dict


def mask_sensitive_fields(
    connection_secrets: Dict[str, Any], secret_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mask sensitive fields in the given secrets based on the provided schema.

    This function traverses the given secrets dictionary and uses the provided schema to
    identify fields that have been marked as sensitive. The function replaces the sensitive
    field values with a mask string ('********').

    Fields not defined in the schema are dropped by default. However, when the schema
    sets ``additionalProperties: true`` (i.e. the Pydantic model uses
    ``extra="allow"``), non-schema fields are preserved as-is. This allows
    connection types like ``jira_ticket`` to store extension-specific config
    (e.g. project_key, templates) alongside the core secrets without requiring
    schema changes in fides for every new field.

    Args:
        connection_secrets: The secrets to be masked.
        secret_schema: The JSON schema defining which fields are sensitive.
    Returns:
        The secrets dictionary with sensitive fields masked.
    """
    if connection_secrets is None:
        return connection_secrets

    secret_schema_properties = secret_schema["properties"]
    allows_additional = secret_schema.get("additionalProperties", False)
    new_connection_secrets = {}

    for key, value in connection_secrets.items():
        if key in secret_schema_properties:
            if secret_schema_properties.get(key, {}).get("sensitive", False):
                new_connection_secrets[key] = "**********"
            else:
                new_connection_secrets[key] = value
        elif allows_additional:
            # Preserve non-schema fields only when the schema explicitly
            # allows additional properties (e.g. extra="allow").
            new_connection_secrets[key] = value

    return new_connection_secrets
