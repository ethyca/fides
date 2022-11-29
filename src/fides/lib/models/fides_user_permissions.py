from typing import List, Tuple

from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.orm import backref, relationship

from fides.lib.db.base_class import Base
from fides.lib.models.fides_user import FidesUser
from fides.lib.oauth.privileges import privileges
from fides.lib.oauth.scopes import PRIVACY_REQUEST_READ


class FidesUserPermissions(Base):
    """The DB ORM model for FidesUserPermissions"""

    user_id = Column(String, ForeignKey(FidesUser.id), nullable=False, unique=True)
    # escaping curly braces requires doubling them. Not a "\". So {{{test123}}}
    # renders as {test123}
    scopes = Column(
        ARRAY(String), nullable=False, default=f"{{{PRIVACY_REQUEST_READ}}}"
    )
    user = relationship(
        FidesUser,
        backref=backref("permissions", cascade="all,delete", uselist=False),
    )

    @property
    def privileges(self) -> Tuple[str, ...]:
        """Return the big-picture privileges a user has based on their individual scopes"""
        user_privileges: List[str] = []
        for privilege, required_scopes in privileges.items():
            if required_scopes.issubset(self.scopes):
                user_privileges.append(privilege)

        return tuple(user_privileges)
