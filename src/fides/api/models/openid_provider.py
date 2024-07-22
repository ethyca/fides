import enum

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import String
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.models.audit_log import AuditLog


class ProviderEnum(enum.Enum):
    google = "google"


class OpenIDProvider(Base):
    """The DB ORM model for OpenIDProvider."""

    provider = Column(EnumColumn(ProviderEnum), unique=True, index=True)
    client_id = Column(String, nullable=False)
    client_secret = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=False)
    disabled = Column(Boolean, nullable=False, server_default="f")

    audit_logs = relationship(
        AuditLog,
        backref="open_id_provider",
        lazy="dynamic",
        passive_deletes="all",
        primaryjoin="foreign(AuditLog.open_id_provider_id)==OpenIDProvider.id",
    )
