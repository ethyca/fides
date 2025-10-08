from typing import Any, Dict


def mask_sensitive_fields(
    connection_secrets: Dict[str, Any], secret_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mask sensitive fields in the given secrets based on the provided schema.
    This function traverses the given secrets dictionary and uses the provided schema to
    identify fields that have been marked as sensitive. The function replaces the sensitive
    field values with a mask string ('********').
    Args:
        connection_secrets (Dict[str, Any]): The secrets to be masked.
        secret_schema (Dict[str, Any]): The schema defining which fields are sensitive.
    Returns:
        Dict[str, Any]: The secrets dictionary with sensitive fields masked.
    """
    if connection_secrets is None:
        return connection_secrets

    secret_schema_properties = secret_schema["properties"]
    new_connection_secrets = {}

    for key, value in connection_secrets.items():
        if key in secret_schema_properties:
            if secret_schema_properties.get(key, {}).get("sensitive", False):
                new_connection_secrets[key] = "**********"
            else:
                new_connection_secrets[key] = value

    return new_connection_secrets
