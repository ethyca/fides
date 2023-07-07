from fides.api.util.connection_util import mask_sensitive_fields


class TestMaskSensitiveFields:
    def test_normal_case(self):
        assert mask_sensitive_fields(
            {"url": "http://example.com", "username": "user", "password": "pass"},
            {
                "properties": {
                    "url": {"sensitive": True},
                    "username": {"sensitive": False},
                    "password": {"sensitive": True},
                }
            },
        ) == {"url": "********", "username": "user", "password": "********"}

    def test_nested_dictionary(self):
        assert mask_sensitive_fields(
            {"database": {"username": "user", "password": "pass"}},
            {
                "properties": {
                    "database": {
                        "properties": {
                            "username": {"sensitive": False},
                            "password": {"sensitive": True},
                        }
                    }
                }
            },
        ) == {"database": {"username": "user", "password": "********"}}

    def test_empty_dictionary(self):
        assert mask_sensitive_fields({}, {"properties": {}}) == {}

    def test_no_sensitive_fields(self):
        assert mask_sensitive_fields(
            {"username": "user", "age": 30},
            {
                "properties": {
                    "username": {"sensitive": False},
                    "age": {"sensitive": False},
                }
            },
        ) == {"username": "user", "age": 30}
