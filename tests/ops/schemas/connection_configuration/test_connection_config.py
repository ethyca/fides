from fides.api.schemas.connection_configuration.connection_config import (
    mask_sensitive_fields,
)


def test_mask_sensitive_fields():
    connection_secrets = {
        "api_id": "secret-test",
        "api_token": "testing with new value",
        "domain": "api.aircall.io",
    }
    secret_schema = {
        "additionalProperties": False,
        "description": "Aircall secrets schema",
        "properties": {
            "api_id": {"sensitive": False, "title": "API ID", "type": "string"},
            "api_token": {"sensitive": True, "title": "API Token", "type": "string"},
            "domain": {
                "default": "api.aircall.io",
                "sensitive": False,
                "title": "Domain",
                "type": "string",
            },
        },
        "required": ["api_id", "api_token"],
        "title": "aircall_schema",
        "type": "object",
    }
    masked_secrets = mask_sensitive_fields(connection_secrets, secret_schema)
    assert masked_secrets == {
        "api_id": "secret-test",
        "api_token": "**********",
        "domain": "api.aircall.io",
    }
