from enum import StrEnum

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from fides.api.db.base_class import Base


class StewardSource(StrEnum):
    """How a monitor steward row was assigned.

    ``explicit`` and ``inherited`` are the values actually persisted to
    ``MonitorSteward.source``. ``both`` is API-only — it's never stored;
    callers building response payloads return it when a user has both an
    explicit and an inherited row for the same monitor.
    """

    explicit = "explicit"
    inherited = "inherited"
    both = "both"


class MonitorSteward(Base):
    """
    Table to link users to monitors as monitor stewards.

    The `source` column distinguishes explicitly assigned stewards from those
    inherited via the monitor's linked system.  A user may appear twice for the
    same monitor — once as explicit and once as inherited — which is why source
    is part of the unique constraint.
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
    source = Column(
        String,
        nullable=False,
        default=StewardSource.explicit.value,
        server_default=StewardSource.explicit.value,
    )
    source_system_id = Column(
        String,
        ForeignKey("ctl_systems.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "monitor_config_id",
            "source",
            name="uq_monitorsteward_user_monitor_source",
        ),
    )
