from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.orm import backref, relationship

from fides.lib.db.base_class import Base
from fides.lib.models.fides_user import FidesUser


class FidesUserPermissions(Base):
    """The DB ORM model for FidesUserPermissions"""

    user_id = Column(String, ForeignKey(FidesUser.id), nullable=False, unique=True)
    scopes = Column(ARRAY(String), nullable=True, server_default="{}", default=dict)
    roles = Column(ARRAY(String), nullable=True, server_default="{}", default=dict)
    user = relationship(
        FidesUser,
        backref=backref("permissions", cascade="all,delete", uselist=False),
    )
