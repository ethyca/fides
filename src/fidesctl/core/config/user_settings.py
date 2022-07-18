"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213

from typing import Dict, Optional

from pydantic import BaseModel, validator

from fidesctl.core.utils import generate_request_headers

from .fides_settings import FidesSettings


class FidesctlUserSettings(FidesSettings):
    """Class used to store values from the 'user' section of the config."""

    user_id: str
    api_key: str
    request_headers: Dict[str, str]
    encryption_key: str
    analytics_opt_out: Optional[bool]

    @staticmethod
    def default() -> "FidesctlUserSettings":
        """Returns config object with default values set."""
        return FidesctlUserSettings(
            user_id="1",
            api_key="test_api_key",
            request_headers=dict(),
            encryption_key="test_encryption_key",
        )

    # Automatically generate the request_headers on object creation
    @validator("request_headers", pre=True, always=True)
    def get_request_headers(
        cls: BaseModel, value: Optional[Dict], values: Dict
    ) -> Dict[str, str]:
        return generate_request_headers(values["user_id"], values["api_key"])

    class Config:
        env_prefix = "FIDESCTL__USER__"
