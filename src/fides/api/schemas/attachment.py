"""Pydantic schemas for data-subject-uploaded attachments."""

from pydantic import ConfigDict, Field

from fides.api.schemas.base_class import FidesSchema


class PrivacyRequestAttachment(FidesSchema):
    """Response payload for the privacy-request attachment upload endpoint.

    The Privacy Center echoes ``id`` back in the custom field's ``value``
    list when the request is submitted — that id is the sole identifier
    the server uses to resolve the upload.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        description=(
            "AttachmentUserProvided row id. Echo this back in the custom "
            "field's value list when the request is submitted."
        ),
    )
