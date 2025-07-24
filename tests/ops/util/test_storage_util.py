import json
from datetime import datetime

import pytest
from bson import ObjectId

from fides.api.schemas.storage.storage import (
    StorageSecretsGCS,
    StorageSecretsS3,
    StorageType,
)
from fides.api.util.storage_util import StorageJSONEncoder, get_schema_for_secrets


class TestStorageUtil:
    def test_get_schema_for_secrets_invalid_storage_type(self):
        with pytest.raises(ValueError):
            get_schema_for_secrets(
                "invalid_storage_type",
                StorageSecretsS3(
                    aws_access_key_id="aws_access_key_id",
                    aws_secret_access_key="aws_secret_access_key",
                ),
            )

        with pytest.raises(ValueError):
            get_schema_for_secrets(
                StorageType.local,
                StorageSecretsS3(
                    aws_access_key_id="aws_access_key_id",
                    aws_secret_access_key="aws_secret_access_key",
                ),
            )

        with pytest.raises(ValueError) as e:
            get_schema_for_secrets(
                StorageType.s3,
                {
                    "aws_access_key_id": "aws_access_key_id",
                    "aws_secret_access_key": "aws_secret_access_key",
                    "fake_key": "aws_secret_access_key",
                },
            )
        assert "Extra inputs are not permitted" in str(e)

    def test_get_schema_for_secrets_s3(self):
        secrets = get_schema_for_secrets(
            "s3",
            StorageSecretsS3(
                aws_access_key_id="aws_access_key_id",
                aws_secret_access_key="aws_secret_access_key",
            ),
        )
        assert secrets.aws_access_key_id == "aws_access_key_id"
        assert secrets.aws_secret_access_key == "aws_secret_access_key"

        secrets = get_schema_for_secrets(
            StorageType.s3,
            StorageSecretsS3(
                aws_access_key_id="aws_access_key_id",
                aws_secret_access_key="aws_secret_access_key",
            ),
        )
        assert secrets.aws_access_key_id == "aws_access_key_id"
        assert secrets.aws_secret_access_key == "aws_secret_access_key"

    def test_get_schema_for_secrets_gcs(self):
        secrets = get_schema_for_secrets(
            StorageType.gcs,
            StorageSecretsGCS(
                type="service_account",
                project_id="test-project-123",
                private_key_id="test-key-id-456",
                private_key=(
                    "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n"
                ),
                client_email="test-service@test-project-123.iam.gserviceaccount.com",
                client_id="123456789",
                auth_uri="https://accounts.google.com/o/oauth2/auth",
                token_uri="https://oauth2.googleapis.com/token",
                auth_provider_x509_cert_url=(
                    "https://www.googleapis.com/oauth2/v1/certs"
                ),
                client_x509_cert_url=(
                    "https://www.googleapis.com/robot/v1/metadata/x509/"
                    "test-service%40test-project-123.iam.gserviceaccount.com"
                ),
                universe_domain="googleapis.com",
            ),
        )

        assert secrets.type == "service_account"
        assert secrets.project_id == "test-project-123"
        assert secrets.private_key_id == "test-key-id-456"
        assert secrets.private_key == (
            "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n"
        )
        assert (
            secrets.client_email
            == "test-service@test-project-123.iam.gserviceaccount.com"
        )
        assert secrets.client_id == "123456789"
        assert secrets.auth_uri == "https://accounts.google.com/o/oauth2/auth"
        assert secrets.token_uri == "https://oauth2.googleapis.com/token"
        assert secrets.auth_provider_x509_cert_url == (
            "https://www.googleapis.com/oauth2/v1/certs"
        )
        assert secrets.client_x509_cert_url == (
            "https://www.googleapis.com/robot/v1/metadata/x509/"
            "test-service%40test-project-123.iam.gserviceaccount.com"
        )
        assert secrets.universe_domain == "googleapis.com"

    def test_storage_json_encoder(self):
        encoder = StorageJSONEncoder()

        # Test datetime handling
        test_datetime = datetime(2024, 3, 15, 12, 30, 45)
        assert encoder.default(test_datetime) == "2024-03-15T12:30:45"

        # Test ObjectId handling
        test_object_id = ObjectId("507f1f77bcf86cd799439011")
        assert encoder.default(test_object_id) == {"$oid": "507f1f77bcf86cd799439011"}

        # Test fallback to parent encoder for other types
        test_dict = {"key": "value"}
        assert (
            encoder.default(test_dict) == "{'key': 'value'}"
        )  # Should use parent encoder's default handling

    def test_storage_json_encoder_with_object_ids(self):
        """Test that data containing ObjectIds can be serialized using StorageJSONEncoder"""
        test_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "user_id": ObjectId("507f1f77bcf86cd799439012"),
                "name": "test_user",
                "active": True,
            }
        ]

        # This should not raise an error
        serialized = json.dumps(test_data, cls=StorageJSONEncoder)

        # Verify ObjectIds are converted to {"$oid": "..."} format
        assert '{"$oid": "507f1f77bcf86cd799439011"}' in serialized
        assert '{"$oid": "507f1f77bcf86cd799439012"}' in serialized
        assert '"name": "test_user"' in serialized
        assert '"active": true' in serialized

    def test_storage_json_encoder_roundtrip_serialization(self):
        """Test that we can serialize data with ObjectIds and get consistent JSON"""
        test_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "nested": {"user_id": ObjectId("507f1f77bcf86cd799439012")},
                "metadata": {"created": datetime(2024, 3, 15, 12, 30, 45)},
            }
        ]

        # Serialize with StorageJSONEncoder
        serialized = json.dumps(
            test_data, cls=StorageJSONEncoder, separators=(",", ":")
        )

        # Should be able to deserialize with standard json.loads
        deserialized = json.loads(serialized)

        # Check structure is maintained with proper conversions
        assert deserialized[0]["_id"] == {"$oid": "507f1f77bcf86cd799439011"}
        assert deserialized[0]["nested"]["user_id"] == {
            "$oid": "507f1f77bcf86cd799439012"
        }
        assert deserialized[0]["metadata"]["created"] == "2024-03-15T12:30:45"
