import pytest

from fides.api.schemas.connection_configuration.connection_config import (
    mask_sensitive_fields,
)


class TestMaskSensitiveValues:
    @pytest.fixture(scope="function")
    def secret_schema(self):
        return {
            "additionalProperties": False,
            "description": "Aircall secrets schema",
            "properties": {
                "api_id": {"sensitive": False, "title": "API ID", "type": "string"},
                "api_token": {
                    "sensitive": True,
                    "title": "API token",
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
    def secret_schema_with_dataset_references(self):
        return {
            "title": "doordash_schema",
            "description": "Doordash secrets schema",
            "type": "object",
            "properties": {
                "domain": {
                    "title": "Domain",
                    "default": "openapi.doordash.com",
                    "sensitive": False,
                    "type": "string",
                },
                "developer_id": {
                    "title": "Developer ID",
                    "sensitive": False,
                    "type": "string",
                },
                "key_id": {"title": "Key ID", "sensitive": False, "type": "string"},
                "signing_secret": {
                    "title": "Signing secret",
                    "sensitive": True,
                    "type": "string",
                },
                "doordash_delivery_id": {
                    "title": "Doordash Delivery ID",
                    "external_reference": True,
                    "allOf": [{"$ref": "#/definitions/FidesDatasetReference"}],
                },
            },
            "required": [
                "developer_id",
                "key_id",
                "signing_secret",
                "doordash_delivery_id",
            ],
            "additionalProperties": False,
            "definitions": {
                "EdgeDirection": {
                    "title": "EdgeDirection",
                    "description": "Direction of a FidesDataSetReference",
                    "enum": ["from", "to"],
                    "type": "string",
                },
                "FidesDatasetReference": {
                    "title": "FidesDatasetReference",
                    "description": "Reference to a field from another Collection",
                    "type": "object",
                    "properties": {
                        "dataset": {
                            "title": "Dataset",
                            "pattern": "^[a-zA-Z0-9_.<>-]+$",
                            "type": "string",
                        },
                        "field": {"title": "Field", "type": "string"},
                        "direction": {"$ref": "#/definitions/EdgeDirection"},
                    },
                    "required": ["dataset", "field"],
                },
            },
        }

    @pytest.fixture(scope="function")
    def secret_schema_with_nested_sensitive_field(self):
        return {
            "title": "BigQuerySchema",
            "description": "Schema to validate the secrets needed to connect to BigQuery",
            "type": "object",
            "properties": {
                "keyfile_creds": {
                    "title": "Keyfile Creds",
                    "description": "The contents of the key file that contains authentication credentials for a service account in GCP.",
                    "sensitive": True,
                    "allOf": [{"$ref": "#/definitions/KeyfileCreds"}],
                },
                "dataset": {
                    "title": "BigQuery Dataset",
                    "description": "The dataset within your BigQuery project that contains the tables you want to access.",
                    "type": "string",
                },
            },
            "required": ["keyfile_creds", "dataset"],
            "definitions": {
                "KeyfileCreds": {
                    "title": "KeyfileCreds",
                    "description": "Schema that holds BigQuery keyfile key/vals",
                    "type": "object",
                    "properties": {
                        "type": {"title": "Type", "type": "string"},
                        "project_id": {"title": "Project ID", "type": "string"},
                        "private_key_id": {"title": "Private Key ID", "type": "string"},
                        "private_key": {
                            "title": "Private Key",
                            "sensitive": True,
                            "type": "string",
                        },
                        "client_email": {
                            "title": "Client Email",
                            "type": "string",
                            "format": "email",
                        },
                        "client_id": {"title": "Client ID", "type": "string"},
                        "auth_uri": {"title": "Auth URI", "type": "string"},
                        "token_uri": {"title": "Token URI", "type": "string"},
                        "auth_provider_x509_cert_url": {
                            "title": "Auth Provider X509 Cert URL",
                            "type": "string",
                        },
                        "client_x509_cert_url": {
                            "title": "Client X509 Cert URL",
                            "type": "string",
                        },
                    },
                    "required": ["project_id"],
                }
            },
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

    def test_mask_dataset_reference_fields(self, secret_schema_with_dataset_references):
        masked_secrets = mask_sensitive_fields(
            {
                "domain": "openapi.doordash.com",
                "developer_id": "123",
                "key_id": "123",
                "signing_secret": "123",
                "doordash_delivery_id": {
                    "dataset": "shop",
                    "field": "customer.id",
                    "direction": "from",
                },
            },
            secret_schema_with_dataset_references,
        )
        assert masked_secrets == {
            "domain": "openapi.doordash.com",
            "developer_id": "123",
            "key_id": "123",
            "signing_secret": "**********",
            "doordash_delivery_id": {
                "dataset": "shop",
                "field": "customer.id",
                "direction": "from",
            },
        }

    def test_mask_nested_sensitive_field(
        self, secret_schema_with_nested_sensitive_field
    ):
        masked_secrets = mask_sensitive_fields(
            {
                "keyfile_creds": {
                    "type": "service_account",
                    "project_id": "discovery-project",
                    "private_key_id": "KEY_ID",
                    "private_key": "SOME_PRIVATE_KEY",
                    "client_email": "EMAIL",
                    "client_id": "CLIENT_ID",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": "cert_url",
                    "universe_domain": "googleapis.com",
                },
                "dataset": "my_dataset",
            },
            secret_schema_with_nested_sensitive_field,
        )
        assert masked_secrets == {
            "keyfile_creds": "**********",
            "dataset": "my_dataset",
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
