from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableList

from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.models.connectionconfig import ConnectionConfig


class ConsentAutomation(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_consent_automation"

    connection_config_id = Column(
        String,
        ForeignKey(ConnectionConfig.id_field_path, ondelete="CASCADE"),
        nullable=False,
    )
    consentable_items = Column(MutableList.as_mutable(JSONB), nullable=False)
