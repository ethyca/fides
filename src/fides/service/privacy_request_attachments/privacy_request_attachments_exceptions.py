"""Domain exceptions for the attachments service.

Routes catch these and translate to HTTP. Services and repositories must
never raise ``HTTPException`` directly.
"""

from typing import Optional


class AttachmentsServiceError(Exception):
    """Base class for attachments service domain errors."""


class InvalidAttachmentStateError(AttachmentsServiceError):
    """Raised when an attachment is not in the expected lifecycle state."""

    def __init__(self, object_key: str, status: str, expected: str = "uploaded"):
        self.object_key = object_key
        self.status = status
        self.expected = expected
        super().__init__(
            f"Attachment '{object_key}' is in state {status}, "
            f"expected '{expected}'. Refusing to promote."
        )


class StorageNotConfiguredError(AttachmentsServiceError):
    """Raised when no active storage configuration is available."""

    def __init__(self, message: str = "No active storage configured."):
        super().__init__(message)


class StorageBucketNotConfiguredError(AttachmentsServiceError):
    """Raised when the active storage configuration has no bucket set."""

    def __init__(self, message: str = "Storage bucket is not configured."):
        super().__init__(message)


class FileTooLargeError(AttachmentsServiceError):
    """Raised when an upload exceeds the configured ``max_size_bytes``."""

    def __init__(self, max_size_bytes: int):
        self.max_size_bytes = max_size_bytes
        super().__init__(
            f"File exceeds maximum allowed size of {max_size_bytes} bytes."
        )


class DisallowedFileTypeError(AttachmentsServiceError):
    """Raised when an uploaded file's MIME type is not in the per-field allow-list."""

    def __init__(self, allowed: list[str]):
        self.allowed = allowed
        super().__init__(
            f"File type not permitted. Allowed types: {', '.join(allowed)}."
        )


class InvalidAttachmentValueError(AttachmentsServiceError):
    """Raised when a custom-privacy-request file field has a malformed value."""

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Invalid attachment value for field '{field_name}'.")


class AttachmentNotFoundError(AttachmentsServiceError):
    """Raised when a referenced attachment id is missing or not in ``uploaded`` state.

    Distinct from :class:`fidesplus.errors.attachment_errors.AttachmentNotFoundError`,
    which models the not-found case for already-promoted ``Attachment`` records.

    ``reason`` is a free-form short tag (e.g. ``"missing"``, the row's
    current ``status`` value) that callers attach for diagnostic detail
    without leaking row identifiers into the message.
    """

    def __init__(self, field_name: str, reason: str | None = None):
        self.field_name = field_name
        self.reason = reason
        message = f"No pending attachment found for field '{field_name}'."
        if reason:
            message = f"{message} Reason: {reason}."
        super().__init__(message)


class AttachmentContextMismatchError(AttachmentsServiceError):
    """Raised when an attachment's stored context disagrees with the submission.

    Re-checked at promotion time as defense-in-depth: the same id cannot be
    re-submitted under a different field, property, or policy.
    """

    def __init__(
        self,
        *,
        attachment_id: str,
        expected_field: str,
        actual_field: str,
        expected_property: Optional[str],
        actual_property: Optional[str],
        expected_policy: str,
        actual_policy: str,
    ):
        self.attachment_id = attachment_id
        self.expected_field = expected_field
        self.actual_field = actual_field
        self.expected_property = expected_property
        self.actual_property = actual_property
        self.expected_policy = expected_policy
        self.actual_policy = actual_policy
        super().__init__(
            f"Attachment {attachment_id} context mismatch "
            f"(field expected={expected_field!r} actual={actual_field!r}, "
            f"property expected={expected_property!r} actual={actual_property!r}, "
            f"policy expected={expected_policy!r} actual={actual_policy!r})."
        )
