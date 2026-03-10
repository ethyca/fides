from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from fides.api.db.base_class import Base


class MonitorSteward(Base):
    """
    Table to link users to monitors as monitor stewards.
    """

    user_id = Column(
        String,
        ForeignKey("fidesuser.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    monitor_config_id = Column(
        String,
        ForeignKey("monitorconfig.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "monitor_config_id", name="uq_monitorsteward_user_monitor"
        ),
    )
