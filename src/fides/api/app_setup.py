"""
Contains utility functions that set up the application webserver.
"""
from logging import DEBUG
from typing import List, Optional, Pattern, Union

from fastapi import FastAPI
from loguru import logger
from redis.exceptions import RedisError, ResponseError
from slowapi.errors import RateLimitExceeded  # type: ignore
from slowapi.extension import _rate_limit_exceeded_handler  # type: ignore
from slowapi.middleware import SlowAPIMiddleware  # type: ignore
from starlette.middleware.cors import CORSMiddleware

import fides
from fides.api.api.deps import get_api_session
from fides.api.api.v1.api import api_router
from fides.api.api.v1.endpoints.utils import fides_limiter
from fides.api.api.v1.exception_handlers import ExceptionHandlers
from fides.api.common_exceptions import FunctionalityNotConfigured, RedisConnectionError
from fides.api.ctl.database.database import configure_db
from fides.api.ctl.database.seed import create_or_update_parent_user
from fides.api.ctl.routes import CTL_ROUTER
from fides.api.ctl.utils.errors import FidesError
from fides.api.ctl.utils.logger import setup as setup_logging
from fides.api.models.application_config import ApplicationConfig
from fides.api.oauth.utils import get_root_client, verify_oauth_client_prod
from fides.api.service.connectors.saas.connector_registry_service import (
    update_saas_configs,
)

# pylint: disable=wildcard-import, unused-wildcard-import
from fides.api.service.saas_request.override_implementations import *
from fides.api.util.cache import get_cache
from fides.api.util.system_manager_oauth_util import (
    get_system_fides_key,
    get_system_schema,
    verify_oauth_client_for_system_from_fides_key_cli,
    verify_oauth_client_for_system_from_request_body_cli,
)
from fides.core.config import CONFIG

VERSION = fides.__version__

ROUTERS = [CTL_ROUTER, api_router]


def create_fides_app(
    cors_origins: Union[str, List[str]] = CONFIG.security.cors_origins,
    cors_origin_regex: Optional[Pattern] = CONFIG.security.cors_origin_regex,
    routers: List = ROUTERS,
    app_version: str = VERSION,
    security_env: str = CONFIG.security.env,
) -> FastAPI:
    """Return a properly configured application."""
    setup_logging(
        CONFIG.logging.level,
        serialize=CONFIG.logging.serialization,
        desination=CONFIG.logging.destination,
    )
    logger.bind(api_config=CONFIG.logging.json()).debug(
        "Logger configuration options in use"
    )

    fastapi_app = FastAPI(title="fides", version=app_version)
    fastapi_app.state.limiter = fides_limiter
    fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    for handler in ExceptionHandlers.get_handlers():
        fastapi_app.add_exception_handler(FunctionalityNotConfigured, handler)
    fastapi_app.add_middleware(SlowAPIMiddleware)

    if cors_origins or cors_origin_regex:
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in cors_origins],
            allow_origin_regex=cors_origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    for router in routers:
        fastapi_app.include_router(router)

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


async def run_database_startup() -> None:
    """
    Perform all relevant database startup activities/configuration for the
    application webserver.
    """

    if not CONFIG.database.sync_database_uri:
        raise FidesError("No database uri provided")

    if CONFIG.database.automigrate:
        await configure_db(
            CONFIG.database.sync_database_uri, samples=CONFIG.database.load_samples
        )
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

    logger.info("Validating SaaS connector templates...")
    try:
        update_saas_configs(db)
        logger.info("Finished loading SaaS templates")
    except Exception as e:
        logger.error(
            "Error occurred during SaaS connector template validation: {}",
            str(e),
        )
        return
    finally:
        db.close()
    db.close()


def check_redis() -> None:
    """Check that Redis is healthy."""

    logger.info("Running Cache connection test...")

    try:
        get_cache()
    except (RedisConnectionError, RedisError, ResponseError) as e:
        logger.error("Connection to cache failed: {}", str(e))
        return
    else:
        logger.debug("Connection to cache succeeded")
