from typing import List, cast

from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser
from fides.api.oauth.roles import EXTERNAL_RESPONDENT, ROLES_TO_SCOPES_MAPPING


class FidesUserPermissions(Base):
    """The DB ORM model for FidesUserPermissions"""

    user_id = Column(String, ForeignKey(FidesUser.id), nullable=False, unique=True)
    roles = Column(ARRAY(String), nullable=False, server_default="{}", default=dict)
    user = relationship(FidesUser, back_populates="permissions", uselist=False)

    @property
    def total_scopes(self) -> List[str]:
        """Returns the scopes the user has inherited via their roles."""
        all_scopes = []
        for role in self.roles:
            all_scopes += ROLES_TO_SCOPES_MAPPING.get(role, [])

        return sorted(list(set(all_scopes)))

    def is_external_respondent(self) -> bool:
        """Check if the user is a external respondent."""
        return any(role in self.roles for role in [EXTERNAL_RESPONDENT])

    def update_roles(self, db: Session, new_roles: List[str]) -> None:
        """Update the user's roles if allowed.
        Raises ValueError if role changes are not allowed."""
        if self.is_external_respondent():
            raise ValueError("Role changes are not allowed for external respondents")

        self.roles = new_roles
        self.save(db)

    def update(self, db: Session, *, data: dict) -> "FidesUserPermissions":
        """Update the user permissions with the provided data."""
        return cast(FidesUserPermissions, super().update(db, data=data))
