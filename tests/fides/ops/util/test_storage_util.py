import json
from datetime import datetime

import pytest
from bson import ObjectId

from fides.api.schemas.storage.storage import (
    StorageSecretsGCS,
    StorageSecretsS3,
    StorageType,
)
from fides.api.util.storage_util import (
    StorageJSONEncoder,
    format_size,
    get_schema_for_secrets,
)


class TestFormatSize:
    """Tests for the format_size function"""

    @pytest.mark.parametrize(
        "size_bytes,expected",
        [
            # Bytes
            (0, "0.0 B"),
            (1, "1.0 B"),
            (100, "100.0 B"),
            (1023, "1023.0 B"),
            # Kilobytes
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (2048, "2.0 KB"),
            (1048575, "1024.0 KB"),  # 1024^2 - 1 = 1048575 bytes = 1024.0 KB
            # Megabytes
            (1048576, "1.0 MB"),
            (1572864, "1.5 MB"),
            (2097152, "2.0 MB"),
            (1073741823, "1024.0 MB"),  # 1024^3 - 1 = 1073741823 bytes = 1024.0 MB
            # Gigabytes
            (1073741824, "1.0 GB"),
            (1610612736, "1.5 GB"),
            (2147483648, "2.0 GB"),
            (
                1099511627775,
                "1024.0 GB",
            ),  # 1024^4 - 1 = 1099511627775 bytes = 1024.0 GB
            # Terabytes
            (1099511627776, "1.0 TB"),
            (1649267441664, "1.5 TB"),
            (2199023255552, "2.0 TB"),
            (
                1125899906842623,
                "1024.0 TB",
            ),  # 1024^5 - 1 = 1125899906842623 bytes = 1024.0 TB
            # Petabytes
            (1125899906842624, "1.0 PB"),
            (1688849860263936, "1.5 PB"),
            (2251799813685248, "2.0 PB"),
            (10000000000000000, "8.9 PB"),
        ],
    )
    def test_format_size_units(self, size_bytes, expected):
        """Test formatting sizes across all units"""
        assert format_size(size_bytes) == expected

    def test_format_size_boundary_conditions(self):
        """Test exact boundary conditions"""
        assert format_size(1048575) == "1024.0 KB"
        assert format_size(1048576) == "1.0 MB"
        assert format_size(1073741823) == "1024.0 MB"
        assert format_size(1073741824) == "1.0 GB"

    @pytest.mark.parametrize(
        "size_bytes,expected",
        [
            # Float inputs
            (0.0, "0.0 B"),
            (1024.5, "1.0 KB"),
            (1536.0, "1.5 KB"),
            # Very small numbers
            (0.1, "0.1 B"),
            (0.5, "0.5 B"),
            # Very large numbers
            (1000000000000000000, "888.2 PB"),
            # Negative numbers (function doesn't handle negatives properly)
            (-1024, "-1024.0 B"),
            (-1536, "-1536.0 B"),
        ],
    )
    def test_format_size_edge_cases(self, size_bytes, expected):
        """Test edge cases and special inputs"""
        assert format_size(size_bytes) == expected


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
