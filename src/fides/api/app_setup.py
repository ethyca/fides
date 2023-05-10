"""
Contains utility functions that set up the application webserver.
"""
from datetime import datetime, timezone
from logging import DEBUG, WARNING
from typing import Callable, List, Optional, Pattern, Union

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fideslog.sdk.python.event import AnalyticsEvent
from loguru import logger
from redis.exceptions import RedisError, ResponseError
from slowapi.errors import RateLimitExceeded  # type: ignore
from slowapi.extension import Limiter, _rate_limit_exceeded_handler  # type: ignore
from slowapi.middleware import SlowAPIMiddleware  # type: ignore
from slowapi.util import get_remote_address  # type: ignore
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

import fides
from fides.api.ctl import view
from fides.api.ctl.database.database import configure_db
from fides.api.ctl.database.seed import create_or_update_parent_user
from fides.api.ctl.routes import admin, crud, generate, health, system, validate
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.ui import (
    get_admin_index_as_response,
    get_path_to_admin_ui_file,
    get_ui_file_map,
    match_route,
    path_is_in_ui_directory,
)
from fides.api.ctl.utils.errors import FidesError
from fides.api.ctl.utils.logger import setup as setup_logging
from fides.api.ops.analytics import (
    accessed_through_local_host,
    in_docker_container,
    send_analytics_event,
)
from fides.api.ops.api.deps import get_api_session
from fides.api.ops.api.v1.api import api_router
from fides.api.ops.api.v1.exception_handlers import ExceptionHandlers
from fides.api.ops.common_exceptions import (
    FunctionalityNotConfigured,
    RedisConnectionError,
)
from fides.api.ops.models.application_config import ApplicationConfig
from fides.api.ops.schemas.analytics import Event, ExtraData
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    update_saas_configs,
)

# pylint: disable=wildcard-import, unused-wildcard-import
from fides.api.ops.service.privacy_request.email_batch_service import (
    initiate_scheduled_batch_email_send,
)
from fides.api.ops.service.saas_request.override_implementations import *
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import _log_exception
from fides.api.ops.util.oauth_util import get_root_client, verify_oauth_client_prod
from fides.api.ops.util.system_manager_oauth_util import (
    get_system_fides_key,
    get_system_schema,
    verify_oauth_client_for_system_from_fides_key_cli,
    verify_oauth_client_for_system_from_request_body_cli,
)
from fides.cli.utils import FIDES_ASCII_ART
from fides.core.config import CONFIG, check_required_webserver_config_values
from fides.lib.oauth.api.routes.user_endpoints import router as user_router

VERSION = fides.__version__

ROUTERS = crud.routers + [  # type: ignore[attr-defined]
    admin.router,
    generate.router,
    health.router,
    validate.router,
    view.router,
    system.system_connections_router,
    system.system_router,
]


def create_fides_app(
    cors_origins: Union[str, List[str]] = CONFIG.security.cors_origins,
    cors_origin_regex: Optional[Pattern] = CONFIG.security.cors_origin_regex,
    routers: List = ROUTERS,
    app_version: str = VERSION,
    api_prefix: str = API_PREFIX,
    request_rate_limit: str = CONFIG.security.request_rate_limit,
    rate_limit_prefix: str = CONFIG.security.rate_limit_prefix,
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
    fastapi_app.state.limiter = Limiter(
        default_limits=[request_rate_limit],
        headers_enabled=True,
        key_prefix=rate_limit_prefix,
        key_func=get_remote_address,
        retry_after="http-date",
    )
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
    fastapi_app.include_router(api_router)

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

    await configure_db(
        CONFIG.database.sync_database_uri, samples=CONFIG.database.load_samples
    )

    try:
        create_or_update_parent_user()
    except Exception as e:
        logger.error("Error creating parent user: {}", str(e))
        raise FidesError(f"Error creating parent user: {str(e)}")
    logger.info("Loading config settings into database...")
    try:
        db = get_api_session()
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
        db = get_api_session()
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

    if not scheduler.running:
        scheduler.start()
