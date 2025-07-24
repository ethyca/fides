import pytest

from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_mysql import (
    GoogleCloudSQLMySQLSchema,
)
from fides.api.schemas.connection_configuration.enums.google_cloud_sql_ip_type import (
    GoogleCloudSQLIPType,
)


class TestGoogleCloudSQLMySQLSchema:
    """Tests for GoogleCloudSQLMySQLSchema validation and field validators"""

    def test_empty_string_to_none_validator(self):
        """Test the empty_string_to_none validator for ip_type field"""
        # Test with empty string
        result = GoogleCloudSQLMySQLSchema.empty_string_to_none("")
        assert result is None

        # Test with None value
        result = GoogleCloudSQLMySQLSchema.empty_string_to_none(None)
        assert result is None

        # Test with valid IP type
        result = GoogleCloudSQLMySQLSchema.empty_string_to_none("public")
        assert result == GoogleCloudSQLIPType.public

        # Test with invalid IP type
        with pytest.raises(ValueError):
            GoogleCloudSQLMySQLSchema.empty_string_to_none("INVALID_TYPE")
