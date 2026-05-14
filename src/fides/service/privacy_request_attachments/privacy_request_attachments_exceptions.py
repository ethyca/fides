"""Domain exceptions for the attachments service.

Routes catch these and translate to HTTP. Services and repositories must
never raise ``HTTPException`` directly.
"""


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
