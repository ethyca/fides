from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base


class SystemPurpose(Base):
    """
    Audited join table linking a System to a DataPurpose.
    Used by the DataConsumer facade for system-type consumers.
    """

    __tablename__ = "system_purpose"
    __table_args__ = (
        UniqueConstraint("system_id", "data_purpose_id", name="uq_system_purpose"),
    )

    system_id = Column(
        String,
        ForeignKey("ctl_systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_purpose_id = Column(
        String,
        ForeignKey("data_purpose.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_by = Column(
        String,
        ForeignKey("fidesuser.id"),
        nullable=True,
    )

    system = relationship("System", lazy="selectin")
    data_purpose = relationship("DataPurpose", lazy="selectin")
