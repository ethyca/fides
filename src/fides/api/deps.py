from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.common_exceptions import RedisNotConfigured
from fides.api.db.ctl_session import async_session, get_async_db
from fides.api.db.session import get_db_engine, get_db_session
from fides.api.util.cache import get_cache as get_redis_connection
from fides.common.session import (
    get_api_session as get_api_session,
)
from fides.common.session import (
    get_autoclose_db_session as get_autoclose_db_session,
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

_readonly_engine = None


def get_config() -> FidesConfig:
    """Returns the config for use in dependency injection."""
    return get_app_config()


def get_db() -> Generator:
    """Return our database session"""
    try:
        db = get_api_session()
        yield db
    finally:
        db.close()


def get_readonly_db() -> Generator:
    """Return our readonly database session"""
    try:
        db = get_readonly_api_session()
        yield db
    finally:
        db.close()


@contextmanager
def get_readonly_autoclose_db_session() -> Generator[Session, None, None]:
    """
    Return a read-only database session as a context manager that automatically closes.
    Falls back to primary database session if read-only is not configured.

    Use this when you need manual control over the session lifecycle outside of API endpoints.
    """
    if not CONFIG.database.sqlalchemy_readonly_database_uri:
        with get_autoclose_db_session() as db:
            yield db
        return

    try:
        db = get_readonly_api_session()
        yield db
    finally:
        db.close()


def get_readonly_api_session() -> Session:
    """Gets the shared read-only database session to use for API functionality"""
    if not CONFIG.database.sqlalchemy_readonly_database_uri:
        return get_api_session()

    global _readonly_engine  # pylint: disable=W0603
    if not _readonly_engine:
        _readonly_engine = get_db_engine(
            database_uri=CONFIG.database.sqlalchemy_readonly_database_uri,
            pool_size=CONFIG.database.api_engine_pool_size,
            max_overflow=CONFIG.database.api_engine_max_overflow,
            keepalives_idle=CONFIG.database.api_engine_keepalives_idle,
            keepalives_interval=CONFIG.database.api_engine_keepalives_interval,
            keepalives_count=CONFIG.database.api_engine_keepalives_count,
            pool_pre_ping=CONFIG.database.api_engine_pool_pre_ping,
        )
    SessionLocal = get_db_session(CONFIG, engine=_readonly_engine)
    db = SessionLocal()
    return db


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
