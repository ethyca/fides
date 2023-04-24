# Import all the models, so that Base has them before being
# imported by Alembic
# pylint: disable=unused-import
from fides.lib.db.base_class import Base
from fides.api.ops.models.audit_log import AuditLog
from fides.api.ops.models.client import ClientDetail
from fides.api.ops.models.fides_user import FidesUser
from fides.api.ops.models.fides_user_permissions import FidesUserPermissions
