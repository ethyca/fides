from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.data_purpose import DataPurpose
    from fides.api.models.sql_models import System  # type: ignore[attr-defined]


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

    system = relationship("System", lazy="selectin")  # type: ignore[misc]
    data_purpose = relationship("DataPurpose", lazy="selectin")
