"""Domain exceptions for the attachments service.

Routes catch these and translate to HTTP. Services and repositories must
never raise ``HTTPException`` directly.
"""


class AttachmentsServiceError(Exception):
    """Base class for attachments service domain errors."""


class StorageNotConfiguredError(AttachmentsServiceError):
    """Raised when no active default storage config is available."""

    def __init__(self, detail: str = "No active default storage configuration found."):
        self.detail = detail
        super().__init__(detail)


class StorageBucketNotConfiguredError(AttachmentsServiceError):
    """Raised when the active storage config has no bucket set."""

    def __init__(self, detail: str = "Active storage configuration has no bucket."):
        self.detail = detail
        super().__init__(detail)


class FileTooLargeError(AttachmentsServiceError):
    """Raised when an upload exceeds the configured max size."""

    def __init__(self, max_size_bytes: int):
        self.max_size_bytes = max_size_bytes
        super().__init__(f"File exceeds maximum allowed size of {max_size_bytes} bytes")


class DisallowedFileTypeError(AttachmentsServiceError):
    """Raised when an upload's detected file type is not in the allow-list."""

    def __init__(self, allowed_extensions: list[str]):
        self.allowed_extensions = allowed_extensions
        super().__init__(
            f"File type is not allowed. Allowed extensions: {sorted(allowed_extensions)}"
        )


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


class AttachmentNotFoundError(AttachmentsServiceError):
    """Raised when a referenced attachment id can't be locked as ``uploaded``."""

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(
            f"File attachment for field '{field_name}' "
            "has expired or is invalid. Please re-upload and resubmit."
        )


class InvalidAttachmentValueError(AttachmentsServiceError):
    """Raised when a file field's value isn't a list of attachment ids."""

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(
            f"File attachment for field '{field_name}' must be a list of attachment ids."
        )
