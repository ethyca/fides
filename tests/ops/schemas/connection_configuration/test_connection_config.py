from fides.api.schemas.connection_configuration.connection_config import (
    mask_sensitive_fields,
)

import pytest


class TestMaskSenstiveValues:
    @pytest.fixture(scope="function")
    def secret_schema(self):
        return {
            "additionalProperties": False,
            "description": "Aircall secrets schema",
            "properties": {
                "api_id": {"sensitive": False, "title": "API ID", "type": "string"},
                "api_token": {
                    "sensitive": True,
                    "title": "API Token",
                    "type": "string",
                },
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

    @pytest.fixture(scope="function")
    def connection_secrets(self):
        return {
            "api_id": "secret-test",
            "api_token": "testing with new value",
            "domain": "api.aircall.io",
        }

    def test_mask_sensitive_fields(self, secret_schema, connection_secrets):
        masked_secrets = mask_sensitive_fields(connection_secrets, secret_schema)
        assert masked_secrets == {
            "api_id": "secret-test",
            "api_token": "**********",
            "domain": "api.aircall.io",
        }

    def test_mask_sensitive_fields_remove_non_schema_values(
        self, connection_secrets, secret_schema
    ):
        connection_secrets["non_schema_value"] = "this should be removed"
        connection_secrets["another_non_schema_value"] = "this should also be removed"

        masked_secrets = mask_sensitive_fields(connection_secrets, secret_schema)
        keys = masked_secrets.keys()
        assert "non_schema_value" not in keys
        assert "another_non_schema_value" not in keys

    def test_return_none_if_no_secrets(self, secret_schema):
        masked_secrets = mask_sensitive_fields(None, secret_schema)
        assert masked_secrets is None
