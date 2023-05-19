from sqlalchemy import Column, ForeignKey, String

from fides.api.db.base_class import Base


class SystemManager(Base):
    """Many to many table to link users to systems as system managers.

    Usually access via user.systems or system.users instead of via this table directly.
    """

    user_id = Column(
        String, ForeignKey("fidesuser.id", ondelete="CASCADE"), primary_key=True
    )
    system_id = Column(
        String, ForeignKey("ctl_systems.id", ondelete="CASCADE"), primary_key=True
    )
