from .fides_settings import FidesSettings


class AdminUISettings(FidesSettings):
    """Configuration settings for Analytics variables."""

    enabled: bool = True

    class Config:
        env_prefix = "FIDES__ADMIN_UI__"
