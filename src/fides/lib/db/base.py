# Import all the models, so that Base has them before being
# imported by Alembic
# pylint: disable=unused-import
from fideslib.db.base_class import Base
from fideslib.models.audit_log import AuditLog
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions
