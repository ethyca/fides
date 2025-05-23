import pytest
from sqlalchemy import text


@pytest.mark.integration_external
@pytest.mark.integration_mysql
class TestMySQLQueryConfig:
    """
    Verify that the generate_query method of MySQLQueryConfig correctly adjusts
    the columns to process keywords.
    """

    def test_generate_raw_query_with_backticks(self, connection_config_mysql):
        """Test that column names are properly wrapped in backticks in the generated query."""

        # Test with regular column names
        field_list = ["id", "email", "name"]
        filters = {"email": ["test@example.com"]}

        query = connection_config_mysql.generate_raw_query(field_list, filters)
        assert isinstance(query, text)
        assert "`id`" in str(query)
        assert "`email`" in str(query)
        assert "`name`" in str(query)

        # Test with reserved keyword as column name
        field_list = ["select", "from", "where"]
        filters = {"select": ["test"]}

        query = connection_config_mysql.generate_raw_query(field_list, filters)
        assert isinstance(query, text)
        assert "`select`" in str(query)
        assert "`from`" in str(query)
        assert "`where`" in str(query)
