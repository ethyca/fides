from .fides_settings import FidesSettings


class AdminUISettings(FidesSettings):
    """Configuration settings for Analytics variables."""

    enabled: bool = True

    class Config:
        env_prefix = "FIDESOPS__ADMIN_UI__"
