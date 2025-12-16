from sqlalchemy import Column, ForeignKey, String

from fides.api.db.base_class import Base


class MonitorSteward(Base):
    """
    Table to link users to monitors as monitor stewards.

    The `id` column (from Base) is the primary key, allowing for potential future
    flexibility to support multiple relationship types between the same
    user and monitor.
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
