import os
from typing import Any, Dict

from hvac import Client
from loguru import logger

from fides.api.common_exceptions import FidesopsException

params = {
    "VAULT_ADDR": os.environ.get("VAULT_ADDR"),
    "VAULT_NAMESPACE": os.environ.get("VAULT_NAMESPACE"),
    "VAULT_TOKEN": os.environ.get("VAULT_TOKEN"),
}
_environment = os.environ.get("VAULT_ENVIRONMENT", "development")


_client = None
if all(params.values()):
    try:
        _client = Client(
            url=params["VAULT_ADDR"],
            namespace=params["VAULT_NAMESPACE"],
            token=params["VAULT_TOKEN"],
        )
    except Exception as exc:
        raise FidesopsException(f"Unable to create Vault client: {str(exc)}")


def get_secrets(connector: str) -> Dict[str, Any]:
    """Returns a map of secrets for the given connector."""
    secrets_map: Dict[str, Any] = {}

    if not _client:
        return secrets_map

    try:
        secrets = _client.secrets.kv.v2.read_secret_version(
            mount_point=_environment, path=connector
        )
        secrets_map = secrets["data"]["data"]
        logger.info(f'Loading secrets for {connector}: {", ".join(secrets_map.keys())}')
    except Exception as exc:
        logger.error(f"Error retrieving secrets for {connector}: {type(exc).__name__}")
    return secrets_map
