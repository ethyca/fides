"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213

from fideslib.core.config import SecuritySettings


class FidesctlSecuritySettings(SecuritySettings):
    """Configuration settings for Security variables."""

    @staticmethod
    def default() -> "FidesctlSecuritySettings":
        """Returns config object with default values set."""
        return FidesctlSecuritySettings(
            oauth_root_client_secret="testrootclientsecret",
            app_encryption_key="atestencryptionkeythatisvalidlen",
            drp_jwt_secret="testdrpsecret",
            oauth_root_client_id="testrootclientid",
        )

    class Config:
        env_prefix = "FIDESCTL__SECURITY__"
