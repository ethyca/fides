from typing import List

from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.orm import backref, relationship

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser
from fides.api.oauth.roles import ROLES_TO_SCOPES_MAPPING


class FidesUserPermissions(Base):
    """The DB ORM model for FidesUserPermissions"""

    user_id = Column(String, ForeignKey(FidesUser.id), nullable=False, unique=True)
    roles = Column(ARRAY(String), nullable=False, server_default="{}", default=dict)
    user = relationship(
        FidesUser,
        backref=backref("permissions", cascade="all,delete", uselist=False),
    )

    @property
    def total_scopes(self) -> List[str]:
        """Returns the scopes the user has inherited via their roles."""
        all_scopes = []
        for role in self.roles:
            all_scopes += ROLES_TO_SCOPES_MAPPING.get(role, [])

        return sorted(list(set(all_scopes)))
