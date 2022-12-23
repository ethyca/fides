from typing import Any, Dict, List, Optional

from pydantic import BaseConfig, create_model
from sqlalchemy import Column, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session, relationship

from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.lib.db.base_class import Base
from fides.lib.schemas.base_class import BaseSchema


class AccessManualWebhook(Base):
    """Describes a manual datasource that will be used for access requests.

    These data sources are not treated as part of the traversal.  Data uploaded
    for an AccessManualWebhook is passed on as-is to the end user and is
    not consumed as part of the graph.
    """

    connection_config_id = Column(
        String,
        ForeignKey(ConnectionConfig.id_field_path),
        unique=True,
        nullable=False,
    )
    connection_config = relationship(
        ConnectionConfig, back_populates="access_manual_webhook", uselist=False
    )

    fields = Column(MutableList.as_mutable(JSONB), nullable=False)

    @property
    def fields_schema(self) -> BaseSchema:
        """Build a dynamic Pydantic schema from fields defined on this webhook"""

        class Config:
            extra = "forbid"

        field_definitions: Dict[str, Any] = {
            field["dsr_package_label"]: (Optional[str], None)
            for field in self.fields or []
        }

        ManualWebhookValidationModel = create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            __config__=Config,
            **field_definitions,
        )
        return ManualWebhookValidationModel

    @property
    def fields_non_strict_schema(self) -> BaseSchema:
        """Returns a dynamic Pydantic Schema for webhook fields that can keep the overlap between
        fields that are saved and fields that are defined here."""
        schema: BaseSchema = self.fields_schema
        # Extra is set to "ignore" on the BaseConfig
        schema.__config__ = BaseConfig  # type: ignore[misc]
        return schema

    @property
    def empty_fields_dict(self) -> Dict[str, None]:
        """Return a dictionary that maps defined dsr_package_labels to None

        Returned as a default if no data has been uploaded for a privacy request.
        """
        return {
            key: None
            for key in (self.fields_schema.schema().get("properties") or {}).keys()
        }

    @classmethod
    def get_enabled(cls, db: Session) -> List["AccessManualWebhook"]:
        """Get all enabled access manual webhooks with fields"""
        return (
            db.query(cls)
            .filter(
                AccessManualWebhook.connection_config_id == ConnectionConfig.id,
                ConnectionConfig.disabled.is_(False),
                AccessManualWebhook.fields != text("'null'"),
                AccessManualWebhook.fields != "[]",
            )
            .all()
        )
