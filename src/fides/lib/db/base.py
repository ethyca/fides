# Import all the models, so that Base has them before being
# imported by Alembic
# pylint: disable=unused-import
from fides.lib.db.base_class import Base
from fides.lib.models.audit_log import AuditLog
from fides.lib.models.client import ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions
