from fastapi import Depends
from sqlalchemy.orm import Session

from fides.api.api.deps import get_config, get_config_proxy, get_db
from fides.config import FidesConfig
from fides.config.config_proxy import ConfigProxy
from fides.service.dataset.dataset_config_service import DatasetConfigService
from fides.service.dataset.dataset_service import DatasetService
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService
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


def get_taxonomy_service(db: Session = Depends(get_db)) -> TaxonomyService:
    return TaxonomyService(db)
