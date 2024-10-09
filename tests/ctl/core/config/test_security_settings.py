import pytest

from fides.config.security_settings import SecuritySettings


@pytest.mark.unit
class TestSecuritySettings:
    def test_validate_encryption_key_length_default_value(self):
        settings = SecuritySettings()
        assert settings.app_encryption_key == ""

    def test_validate_encryption_key_invalid_length_error(self):
        with pytest.raises(ValueError):
            SecuritySettings(app_encryption_key="bad")

    def test_validate_encryption_key_valid(self):
        key = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        settings = SecuritySettings(app_encryption_key=key)
        assert settings.app_encryption_key == key

    def test_validate_assemble_cors_origins_invalid_url(self):
        with pytest.raises(ValueError) as err:
            SecuritySettings(cors_origins="123")

        assert "not a valid url" in str(err.value)

    def test_validate_assemble_cors_origins_invalid_type(self):
        with pytest.raises(ValueError):
            SecuritySettings(cors_origins=123)

    def test_validate_assemble_cors_origins_string_of_urls(self):
        urls = ["http://localhost.com", "http://test.com"]
        settings = SecuritySettings(cors_origins=", ".join(urls))

        assert settings.cors_origins == urls

    def test_validate_cors_origins_urls_with_paths(self):
        with pytest.raises(ValueError) as e:
            SecuritySettings(cors_origins=["http://test.com/longerpath"])

        assert "URL origin values cannot contain a path." in str(e)

        with pytest.raises(ValueError) as e:
            SecuritySettings(cors_origins=["http://test.com/123/456"])

        assert "URL origin values cannot contain a path." in str(e)

        # If there is a trailing slash, it is now stripped off
        settings = SecuritySettings(cors_origins=["http://test.com/"])
        assert settings.cors_origins == ["http://test.com"]

    def test_assemble_root_access_token_none(self):
        settings = SecuritySettings(oauth_root_client_secret="")

        assert settings.oauth_root_client_secret_hash is None

    def test_validate_request_rate_limit_invalid_format(self):
        with pytest.raises(ValueError):
            SecuritySettings(request_rate_limit="invalid")

    def test_security_settings_env_default_to_prod(self):
        settings = SecuritySettings()
        assert settings.env == "prod"
