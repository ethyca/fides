# pylint: disable=W0611
# Import all the models, so that Base has them before being
# imported by Alembic
from fides.api.ops.db.base_class import Base
from fides.api.ops.models.application_config import ApplicationConfig
from fides.api.ops.models.audit_log import AuditLog
from fides.api.ops.models.authentication_request import AuthenticationRequest
from fides.api.ops.models.client import ClientDetail
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.custom_connector_template import CustomConnectorTemplate
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.fides_user import FidesUser
from fides.api.ops.models.fides_user_permissions import FidesUserPermissions
from fides.api.ops.models.manual_webhook import AccessManualWebhook
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.models.policy import Policy, Rule, RuleTarget
from fides.api.ops.models.privacy_experience import (
    PrivacyExperience,
    PrivacyExperienceHistory,
    PrivacyExperienceTemplate,
)
from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeHistory
from fides.api.ops.models.privacy_preference import (
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
)
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.models.registration import UserRegistration
from fides.api.ops.models.storage import StorageConfig
from fides.api.ops.models.system_manager import SystemManager
