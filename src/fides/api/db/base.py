# pylint: disable=W0611
# Import all the models, so that Base has them before being
# imported by Alembic
from fides.api.db.base_class import Base
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.audit_log import AuditLog
from fides.api.models.authentication_request import AuthenticationRequest
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.custom_asset import CustomAsset
from fides.api.models.custom_connector_template import CustomConnectorTemplate
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.fides_cloud import FidesCloud
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import MessagingTemplate
from fides.api.models.policy import Policy, Rule, RuleTarget
from fides.api.models.privacy_experience import (
    PrivacyExperience,
    PrivacyExperienceConfig,
    PrivacyExperienceConfigHistory,
)
from fides.api.models.privacy_notice import (
    PrivacyNotice,
    PrivacyNoticeHistory,
    PrivacyNoticeTemplate,
)
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    LastServedNotice,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.registration import UserRegistration
from fides.api.models.storage import StorageConfig
from fides.api.models.system_history import SystemHistory
from fides.api.models.system_manager import SystemManager
