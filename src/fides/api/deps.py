from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.common_exceptions import RedisNotConfigured
from fides.api.db.ctl_session import async_session, get_async_db
from fides.api.util.cache import get_cache as get_redis_connection
from fides.common.session_management import (
    get_api_session,
    get_db,
    get_readonly_api_session,
)
from fides.config import CONFIG, FidesConfig
from fides.config import get_config as get_app_config
from fides.config.config_proxy import ConfigProxy
from fides.service.connection.connection_service import ConnectionService
from fides.service.dataset.dataset_config_service import DatasetConfigService
from fides.service.dataset.dataset_service import DatasetService
from fides.service.event_audit_service import EventAuditService
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService
from fides.service.system.system_service import SystemService
from fides.service.taxonomy.taxonomy_service import TaxonomyService
from fides.service.user.user_service import UserService


def get_config() -> FidesConfig:
    """Returns the config for use in dependency injection."""
    return get_app_config()


def get_readonly_db() -> Generator:
    """Return our readonly database session"""
    try:
        db = get_readonly_api_session()
        yield db
    finally:
        db.close()


def get_config_proxy(db: Session = Depends(get_db)) -> ConfigProxy:
    return ConfigProxy(db)


def get_cache() -> Generator:
    """Return a connection to our Redis cache"""
    if not CONFIG.redis.enabled:
        raise RedisNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a Redis cache."
        )
    yield get_redis_connection()


@asynccontextmanager
async def get_async_autoclose_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Return an async database session as an async context manager that automatically closes when the context exits.

    Use this when you need manual control over the async session lifecycle outside of API endpoints.
    """
    session = async_session()
    try:
        yield session
    finally:
        await session.close()


# ---------------------------------------------------------------------------
# Service factory functions for FastAPI dependency injection.
# ---------------------------------------------------------------------------


def get_messaging_service(
    db: Session = Depends(get_db),
    config: FidesConfig = Depends(get_config),
    config_proxy: ConfigProxy = Depends(get_config_proxy),
) -> MessagingService:
    return MessagingService(db, config, config_proxy)


def get_privacy_request_service(
    db: Session = Depends(get_db),
    config_proxy: ConfigProxy = Depends(get_config_proxy),
    messaging_service: MessagingService = Depends(get_messaging_service),
) -> PrivacyRequestService:
    return PrivacyRequestService(db, config_proxy, messaging_service)


def get_dataset_service(
    db: Session = Depends(get_db),
) -> DatasetService:
    return DatasetService(db)


def get_dataset_config_service(
    db: Session = Depends(get_db),
) -> DatasetConfigService:
    return DatasetConfigService(db)


def get_user_service(
    db: Session = Depends(get_db),
    config: FidesConfig = Depends(get_config),
    config_proxy: ConfigProxy = Depends(get_config_proxy),
    messaging_service: MessagingService = Depends(get_messaging_service),
) -> UserService:
    return UserService(db, config, config_proxy, messaging_service)


def get_event_audit_service(
    db: Session = Depends(get_db),
) -> EventAuditService:
    return EventAuditService(db)


def get_taxonomy_service(
    db: Session = Depends(get_db),
    event_audit_service: EventAuditService = Depends(get_event_audit_service),
) -> TaxonomyService:
    return TaxonomyService(db, event_audit_service)


def get_connection_service(
    db: Session = Depends(get_db),
    event_audit_service: EventAuditService = Depends(get_event_audit_service),
) -> ConnectionService:
    return ConnectionService(db, event_audit_service)


def get_system_service(
    db: AsyncSession = Depends(get_async_db),
) -> SystemService:
    return SystemService(db)
