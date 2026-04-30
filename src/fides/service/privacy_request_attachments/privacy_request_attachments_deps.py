"""Dependency-injection factory for the attachments service."""

from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
    AttachmentUserProvidedService,
)


def get_attachment_user_provided_service() -> AttachmentUserProvidedService:
    return AttachmentUserProvidedService()
