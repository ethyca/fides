from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base


class Control(Base):
    """A regulatory framework or compliance grouping that policies can be associated with."""

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_control"

    key = Column(String, nullable=False, unique=True, index=True)
    label = Column(String, nullable=False)


class AccessPolicyControl(Base):
    """Association between an access policy and a control."""

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_access_policy_control"

    access_policy_id = Column(
        String(255),
        ForeignKey(
            "plus_access_policy.id",
            name="plus_access_policy_control_policy_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    control_id = Column(
        String(255),
        ForeignKey(
            "plus_control.id",
            name="plus_access_policy_control_control_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "access_policy_id",
            name="uq_plus_access_policy_control_one_per_policy",
        ),
    )


class AccessPolicy(Base):
    """Stable entity representing an access policy.

    The FE interacts with this ID for all CRUD operations.
    Actual policy content lives in AccessPolicyVersion rows.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_access_policy"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True, server_default="t")
    is_deleted = Column(Boolean, nullable=False, default=False, server_default="f")

    versions = relationship(
        "AccessPolicyVersion",
        back_populates="access_policy",
        cascade="all, delete-orphan",
        order_by="AccessPolicyVersion.version.desc()",
    )

    controls = relationship(
        "Control",
        secondary=AccessPolicyControl.__table__,
        lazy="selectin",
    )


class AccessPolicyVersion(Base):
    """Immutable snapshot of a policy at a point in time.

    Each update to an AccessPolicy creates a new version row.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_access_policy_version"

    access_policy_id = Column(
        String(255),
        ForeignKey(
            "plus_access_policy.id",
            name="plus_access_policy_version_policy_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    version = Column(Integer, nullable=False, default=1)
    yaml = Column(Text, nullable=False)

    access_policy = relationship(
        "AccessPolicy",
        back_populates="versions",
    )

    __table_args__ = (
        Index(
            "ix_plus_access_policy_version_policy_version",
            "access_policy_id",
            "version",
            unique=True,
        ),
    )
