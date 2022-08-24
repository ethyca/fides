"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from typing import Dict

from fideslib.core.config import SecuritySettings
from fideslib.cryptography.cryptographic_util import generate_salt, hash_with_salt
from pydantic import root_validator


class FidesctlSecuritySettings(SecuritySettings):
    """Configuration settings for Security variables."""

    oauth_root_client_secret: str = "testrootclientsecret"
    app_encryption_key: str = "atestencryptionkeythatisvalidlen"
    drp_jwt_secret: str = "testdrpsecret"
    oauth_root_client_id: str = "testrootclientid"
    encoding: str = "UTF-8"

    @root_validator(pre=True)
    @classmethod
    def assemble_root_access_token(cls, values: Dict[str, str]) -> Dict[str, str]:
        """
        Override SecuritySettings root validator to set secret hash.
        SecuritySettings expects oauth_root_client_secret to be set while
        fidesctl config is expected to work with class defaults.
        """
        value = values.get("oauth_root_client_secret") or "testrootclientsecret"
        encoding = values.get("encoding", "UTF-8")

        salt = generate_salt()
        hashed_client_id = hash_with_salt(value.encode(encoding), salt.encode(encoding))
        values["oauth_root_client_secret_hash"] = (hashed_client_id, salt.encode(encoding))  # type: ignore
        return values

    class Config:
        env_prefix = "FIDESCTL__SECURITY__"
