from fideslib.core.config import SecuritySettings


class FidesctlSecuritySettings(SecuritySettings):
    """Configuration settings for Security variables."""

    class Config:
        env_prefix = "FIDESCTL__SECURITY__"
