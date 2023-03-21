from typing import List

from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.orm import backref, relationship

from fides.lib.db.base_class import Base
from fides.lib.models.fides_user import FidesUser
from fides.lib.oauth.roles import ROLES_TO_SCOPES_MAPPING


class FidesUserPermissions(Base):
    """The DB ORM model for FidesUserPermissions"""

    user_id = Column(String, ForeignKey(FidesUser.id), nullable=False, unique=True)
    scopes = Column(ARRAY(String), nullable=False, server_default="{}", default=dict)
    roles = Column(ARRAY(String), nullable=False, server_default="{}", default=dict)
    user = relationship(
        FidesUser,
        backref=backref("permissions", cascade="all,delete", uselist=False),
    )

    @property
    def total_scopes(self) -> List[str]:
        """Returns the total model-level scopes the user has, either 1) scopes they are assigned directly,
        or 2) Roles they have via their scopes."""
        all_scopes = self.scopes.copy() or []
        for role in self.roles:
            all_scopes += ROLES_TO_SCOPES_MAPPING.get(role, [])

        return sorted(list(set(all_scopes)))
