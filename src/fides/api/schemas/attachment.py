"""Pydantic schemas for data-subject-uploaded attachments."""

from pydantic import ConfigDict, Field

from fides.api.schemas.base_class import FidesSchema


class PrivacyRequestAttachment(FidesSchema):
    """Upload response — echo ``id`` back in the custom field's ``value``."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="AttachmentUserProvided row id.")
