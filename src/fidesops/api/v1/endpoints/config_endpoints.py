import logging
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.params import Security

from fidesops.api.v1 import scope_registry as scopes
from fidesops.api.v1 import urn_registry as urls
from fidesops.core.config import censored_config
from fidesops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Config"], prefix=urls.V1_URL_PREFIX)

logger = logging.getLogger(__name__)


@router.get(
    urls.CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.CONFIG_READ])],
    response_model=Dict[str, Any],
)
def get_config() -> Dict[str, Any]:
    """Returns the current API exposable Fidesops configuration."""
    logger.info("Getting the exposable Fidesops configuration")
    return censored_config
