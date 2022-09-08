# pylint: disable=W0611
# Import all the models, so that Base has them before being
# imported by Alembic
from fideslib.db.base_class import Base
from fideslib.models.audit_log import AuditLog
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions

from fidesops.ops.models.authentication_request import AuthenticationRequest
from fidesops.ops.models.connectionconfig import ConnectionConfig
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.models.email import EmailConfig
from fidesops.ops.models.manual_webhook import AccessManualWebhook
from fidesops.ops.models.policy import Policy, Rule, RuleTarget
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.models.storage import StorageConfig
