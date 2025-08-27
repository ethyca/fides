"""
Contains utility functions that set up the application webserver.
"""

# pylint: disable=too-many-branches
from logging import DEBUG
from typing import AsyncGenerator, List

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute
from loguru import logger
from redis.exceptions import RedisError, ResponseError
from slowapi.errors import RateLimitExceeded  # type: ignore
from slowapi.extension import _rate_limit_exceeded_handler  # type: ignore
from slowapi.middleware import SlowAPIMiddleware  # type: ignore

import fides
from fides.api.api.deps import (
    get_api_session,
    get_async_autoclose_db_session,
    get_autoclose_db_session,
)
from fides.api.api.v1 import CTL_ROUTER
from fides.api.api.v1.api import api_router
from fides.api.api.v1.endpoints.admin import ADMIN_ROUTER
from fides.api.api.v1.endpoints.generic_overrides import GENERIC_OVERRIDES_ROUTER
from fides.api.api.v1.endpoints.health import HEALTH_ROUTER
from fides.api.api.v1.exception_handlers import ExceptionHandlers
from fides.api.common_exceptions import RedisConnectionError, RedisNotConfigured
from fides.api.db import seed
from fides.api.db.database import configure_db, seed_db
from fides.api.db.seed import create_or_update_parent_user
from fides.api.models.application_config import ApplicationConfig
from fides.api.oauth.system_manager_oauth_util import (
    get_system_fides_key,
    get_system_schema,
    verify_oauth_client_for_system_from_fides_key_cli,
    verify_oauth_client_for_system_from_request_body_cli,
)
from fides.api.oauth.utils import get_root_client, verify_oauth_client_prod
from fides.api.service.connectors.saas.connector_registry_service import (
    update_saas_configs,
)

# pylint: disable=wildcard-import, unused-wildcard-import
from fides.api.service.saas_request.override_implementations import *
from fides.api.util.api_router import APIRouter
from fides.api.util.cache import get_cache
from fides.api.util.consent_util import create_default_tcf_purpose_overrides_on_startup
from fides.api.util.endpoint_utils import fides_limiter
from fides.api.util.errors import FidesError
from fides.api.util.logger import setup as setup_logging
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy

VERSION = fides.__version__

# DB_ROUTER holds routers that have direct DB dependencies.
# these routers are initialized _outside_ of inner `api` module
# to avoid cyclical dependency chains.
# see https://github.com/ethyca/fides/issues/3652
DB_ROUTER = APIRouter()
DB_ROUTER.include_router(ADMIN_ROUTER)
DB_ROUTER.include_router(HEALTH_ROUTER)


ROUTERS = [CTL_ROUTER, api_router, DB_ROUTER]
OVERRIDING_ROUTERS = [GENERIC_OVERRIDES_ROUTER]


def create_fides_app(
    lifespan: AsyncGenerator[None, None],
    routers: List = ROUTERS,
    app_version: str = VERSION,
    security_env: str = CONFIG.security.env,
) -> FastAPI:
    """Return a properly configured application."""
    setup_logging(CONFIG)
    logger.bind(api_config=CONFIG.logging.json()).debug(
        "Logger configuration options in use"
    )

    fastapi_app = FastAPI(title="fides", version=app_version, lifespan=lifespan, separate_input_output_schemas=False)  # type: ignore
    fastapi_app.state.limiter = fides_limiter
    # Starlette bug causing this to fail mypy
    fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore
    for handler in ExceptionHandlers.get_handlers():
        # Starlette bug causing this to fail mypy
        fastapi_app.add_exception_handler(RedisNotConfigured, handler)  # type: ignore
    fastapi_app.add_middleware(SlowAPIMiddleware)
    fastapi_app.add_middleware(
        GZipMiddleware, minimum_size=1000, compresslevel=5
    )  # minimum_size is in bytes

    for router in routers:
        fastapi_app.include_router(router)

    override_generic_routers(OVERRIDING_ROUTERS, fastapi_app)

    if security_env == "dev":
        # This removes auth requirements for specific endpoints
        fastapi_app.dependency_overrides[verify_oauth_client_prod] = get_root_client
        fastapi_app.dependency_overrides[
            verify_oauth_client_for_system_from_request_body_cli
        ] = get_system_schema
        fastapi_app.dependency_overrides[
            verify_oauth_client_for_system_from_fides_key_cli
        ] = get_system_fides_key
    elif security_env == "prod":
        # This is the most secure, so all security deps are maintained
        pass

    return fastapi_app


def override_generic_routers(
    overriding_routers: List[APIRouter], base_router: FastAPI
) -> None:
    """
    Remove generic routes in favor of their more specific implementations, if available.
    """
    for i, existing_route in reversed(list(enumerate(base_router.routes))):
        if not isinstance(existing_route, APIRoute):
            continue
        for new_router in overriding_routers:
            for new_route in new_router.routes:
                if not isinstance(new_route, APIRoute):  # pragma: no cover
                    continue
                if (
                    existing_route.methods == new_route.methods
                    and existing_route.path == new_route.path
                ):
                    logger.debug(
                        "Removing generic route: {} {}",
                        existing_route.methods,
                        existing_route.path,
                    )
                    del base_router.routes[i]
    for router in overriding_routers:
        base_router.include_router(router)


def log_startup() -> None:
    """Log application startup and other information."""
    logger.info(f"Starting Fides - v{VERSION}")
    logger.info(
        "Startup configuration: reloading = {}, dev_mode = {}",
        CONFIG.hot_reloading,
        CONFIG.dev_mode,
    )
    logger.info("Startup configuration: pii logging = {}", CONFIG.logging.log_pii)

    if CONFIG.logging.level == DEBUG:
        logger.warning(
            "WARNING: log level is DEBUG, so sensitive or personal data may be logged. "
            "Set FIDES__LOGGING__LEVEL to INFO or higher in production."
        )
        CONFIG.log_all_config_values()


async def run_database_startup(app: FastAPI) -> None:
    """
    Perform all relevant database startup activities/configuration for the
    application webserver.
    """

    if not CONFIG.database.sync_database_uri:
        raise FidesError("No database uri provided")

    if CONFIG.database.automigrate:
        try:
            configure_db(CONFIG.database.sync_database_uri)
            if not CONFIG.test_mode:
                with get_autoclose_db_session() as session:
                    seed_db(session)
            if CONFIG.database.load_samples:
                async with get_async_autoclose_db_session() as async_session:
                    await seed.load_samples(async_session)
        except Exception as e:
            logger.error("Error occurred during database configuration: {}", str(e))
    else:
        logger.info("Skipping auto-migration due to 'automigrate' configuration value.")

    try:
        create_or_update_parent_user()
    except Exception as e:
        logger.error("Error creating parent user: {}", str(e))
        raise FidesError(f"Error creating parent user: {str(e)}")

    db = get_api_session()
    logger.info("Loading config settings into database...")
    try:
        ApplicationConfig.update_config_set(db, CONFIG)
    except Exception as e:
        logger.error("Error occurred writing config settings to database: {}", str(e))
        raise FidesError(
            f"Error occurred writing config settings to database: {str(e)}"
        )
    finally:
        db.close()

    logger.info("Loading CORS domains from ConfigProxy...")
    try:
        ConfigProxy(db).load_current_cors_domains_into_middleware(app)
    except Exception as e:
        logger.error("Error occurred while loading CORS domains: {}", str(e))
        raise FidesError(f"Error occurred while loading CORS domains: {str(e)}")
    finally:
        db.close()

    logger.info("Validating SaaS connector templates...")
    try:
        update_saas_configs(db)
        logger.info("Finished loading SaaS templates")
    except Exception as e:
        logger.exception(
            "Error occurred during SaaS connector template validation: {}",
            str(e),
        )
        return
    finally:
        db.close()

    if not CONFIG.test_mode:
        # Avoiding loading consent out-of-the-box resources to avoid interfering with unit tests
        load_tcf_purpose_overrides()

    db.close()


def check_redis() -> None:
    """Check that Redis is healthy."""
    logger.info("Running Cache connection test...")
    try:
        get_cache()
    except (RedisConnectionError, RedisError, ResponseError) as e:
        logger.error("Connection to cache failed: {}", str(e))
        return

    logger.debug("Connection to cache succeeded")


def load_tcf_purpose_overrides() -> None:
    """Load default tcf purpose overrides"""
    logger.info("Loading default TCF Purpose Overrides")
    try:
        db = get_api_session()
        create_default_tcf_purpose_overrides_on_startup(db)
    except Exception as e:
        logger.error("Skipping loading TCF Purpose Overrides: {}", str(e))
    finally:
        db.close()
