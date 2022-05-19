from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.orm import backref, relationship

from fidesops.api.v1.scope_registry import PRIVACY_REQUEST_READ
from fidesops.db.base_class import Base
from fidesops.models.fidesops_user import FidesopsUser


class FidesopsUserPermissions(Base):
    """The DB ORM model for FidesopsUserPermissions"""

    user_id = Column(String, ForeignKey(FidesopsUser.id), nullable=False, unique=True)
    # escaping curly braces requires doubling them. Not a "\". So {{{test123}}} renders as {test123}
    scopes = Column(
        ARRAY(String), nullable=False, default=f"{{{PRIVACY_REQUEST_READ}}}"
    )
    user = relationship(
        FidesopsUser,
        backref=backref("permissions", cascade="all,delete", uselist=False),
    )
