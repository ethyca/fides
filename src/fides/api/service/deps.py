from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.api.deps import get_config, get_config_proxy, get_db
from fides.api.db.ctl_session import get_async_db
from fides.config import FidesConfig
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


def get_dataset_service(db: Session = Depends(get_db)) -> DatasetService:
    return DatasetService(db)


def get_dataset_config_service(db: Session = Depends(get_db)) -> DatasetConfigService:
    return DatasetConfigService(db)


def get_user_service(
    db: Session = Depends(get_db),
    config: FidesConfig = Depends(get_config),
    config_proxy: ConfigProxy = Depends(get_config_proxy),
) -> UserService:
    return UserService(db, config, config_proxy)


def get_event_audit_service(db: Session = Depends(get_db)) -> EventAuditService:
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


def get_system_service(db: AsyncSession = Depends(get_async_db)) -> SystemService:
    return SystemService(db)
