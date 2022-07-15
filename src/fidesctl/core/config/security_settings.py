from fideslib.core.config import SecuritySettings


class FidesctlSecuritySettings(SecuritySettings):
    """Configuration settings for Security variables."""

    @staticmethod
    def default() -> "FidesctlSecuritySettings":
        return FidesctlSecuritySettings(
            oauth_root_client_secret="testrootclientsecret",
            app_encryption_key="atestencryptionkeythatisvalidlen",
            drp_jwt_secret="testdrpsecret",
            oauth_root_client_id="testrootclientid",
        )

    class Config:
        env_prefix = "FIDESCTL__SECURITY__"
