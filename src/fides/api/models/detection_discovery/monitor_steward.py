from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)

from fides.api.db.base_class import Base


class StewardSource(StrEnum):
    """Persisted values for ``MonitorSteward.source``.

    DB-side enum only — response-layer attribution values are defined
    separately in the API schema.
    """

    explicit = "explicit"
    inherited = "inherited"


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
        server_default=text("'explicit'"),
    )
    source_system_id = Column(
        String,
        # CASCADE (not SET NULL) because inherited rows are derived state:
        # when the source system goes away, the derivation is meaningless.
        # SET NULL would also violate ck_monitorsteward_inherited_has_system,
        # blocking the parent system delete entirely.
        ForeignKey("ctl_systems.id", ondelete="CASCADE"),
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
        CheckConstraint(
            "source IN ('explicit', 'inherited')",
            name="ck_monitorsteward_source_values",
        ),
        CheckConstraint(
            "source != 'inherited' OR source_system_id IS NOT NULL",
            name="ck_monitorsteward_inherited_has_system",
        ),
    )
