from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, create_model
from sqlalchemy import Column, ForeignKey, String, or_, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType


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

    def access_field_definitions(self) -> Dict[str, Any]:
        """Shared access field definitions for manual webhook schemas"""
        return {
            field["dsr_package_label"]: (Optional[str], None)
            for field in self.fields or []
        }

    def erasure_field_definitions(self) -> Dict[str, Any]:
        """Shared erasure field definitions for manual webhook schemas"""
        return {
            field["dsr_package_label"]: (Optional[bool], None)
            for field in self.fields or []
        }

    @property
    def fields_schema(self) -> FidesSchema:
        """Build a dynamic Pydantic schema from fields defined on this webhook"""

        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            __config__=ConfigDict(extra="forbid"),
            **self.access_field_definitions(),
        )

    @property
    def erasure_fields_schema(self) -> FidesSchema:
        """
        Build a dynamic Pydantic schema from fields defined on this webhook.
        The fields in the schema for erasure input validation are of type bool,
        vs str for access input validation.
        """
        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            model_config=ConfigDict(extra="forbid"),
            **self.erasure_field_definitions(),
        )

    @property
    def fields_non_strict_schema(self) -> FidesSchema:
        """Returns a dynamic Pydantic Schema for webhook fields that can keep the overlap between
        fields that are saved and fields that are defined here."""
        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            __config__=ConfigDict(extra="ignore"),
            **self.access_field_definitions(),
        )

    @property
    def erasure_fields_non_strict_schema(self) -> FidesSchema:
        """Returns a dynamic Pydantic Schema for webhook fields that can keep the overlap between
        fields that are saved and fields that are defined here."""
        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            model_config=ConfigDict(extra="ignore"),
            **self.erasure_field_definitions(),
        )

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
    def get_enabled(
        cls, db: Session, action_type: Optional[ActionType] = None
    ) -> List["AccessManualWebhook"]:
        """Get all enabled access manual webhooks with fields"""

        query = db.query(cls).filter(
            AccessManualWebhook.connection_config_id == ConnectionConfig.id,
            ConnectionConfig.disabled.is_(False),
            AccessManualWebhook.fields != text("'null'"),
            AccessManualWebhook.fields != "[]",
        )

        # Add action_type filter only if action_type is provided
        if action_type is not None:
            query = query.filter(
                or_(
                    ConnectionConfig.enabled_actions.contains([action_type]),
                    ConnectionConfig.enabled_actions.is_(None),
                )
            )

        return query.all()
