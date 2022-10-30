# pylint: disable=W0611
# Import all the models, so that Base has them before being
# imported by Alembic
from fideslib.db.base_class import Base
from fideslib.models.audit_log import AuditLog
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions

from fides.api.ops.models.authentication_request import AuthenticationRequest
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.email import EmailConfig
from fides.api.ops.models.manual_webhook import AccessManualWebhook
from fides.api.ops.models.policy import Policy, Rule, RuleTarget
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.models.registration import UserRegistration
from fides.api.ops.models.storage import StorageConfig
