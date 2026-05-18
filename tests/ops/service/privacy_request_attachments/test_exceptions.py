"""Tests for attachments service domain exceptions."""

import pytest

from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    AttachmentContextMismatchError,
    AttachmentNotFoundError,
    AttachmentsServiceError,
    DisallowedFileTypeError,
    FileTooLargeError,
    InvalidAttachmentStateError,
    InvalidAttachmentValueError,
    StorageBucketNotConfiguredError,
    StorageNotConfiguredError,
)


@pytest.mark.unit
class TestInvalidAttachmentStateError:
    def test_message_and_attributes(self):
        exc = InvalidAttachmentStateError("key/path.pdf", "deleted")
        assert exc.object_key == "key/path.pdf"
        assert exc.status == "deleted"
        assert exc.expected == "uploaded"
        assert "key/path.pdf" in str(exc)
        assert "deleted" in str(exc)
        assert "uploaded" in str(exc)

    def test_custom_expected(self):
        exc = InvalidAttachmentStateError("k", "promoted", expected="deleted")
        assert exc.expected == "deleted"

    def test_is_attachments_service_error(self):
        assert isinstance(
            InvalidAttachmentStateError("k", "s"), AttachmentsServiceError
        )


@pytest.mark.unit
class TestStorageNotConfiguredError:
    def test_default_message(self):
        exc = StorageNotConfiguredError()
        assert "No active storage configured" in str(exc)

    def test_custom_message(self):
        exc = StorageNotConfiguredError("custom msg")
        assert str(exc) == "custom msg"

    def test_is_attachments_service_error(self):
        assert isinstance(StorageNotConfiguredError(), AttachmentsServiceError)


@pytest.mark.unit
class TestStorageBucketNotConfiguredError:
    def test_default_message(self):
        exc = StorageBucketNotConfiguredError()
        assert "Storage bucket is not configured" in str(exc)

    def test_custom_message(self):
        exc = StorageBucketNotConfiguredError("override")
        assert str(exc) == "override"

    def test_is_attachments_service_error(self):
        assert isinstance(StorageBucketNotConfiguredError(), AttachmentsServiceError)


@pytest.mark.unit
class TestFileTooLargeError:
    def test_message_contains_limit(self):
        exc = FileTooLargeError(5_000_000)
        assert "5000000" in str(exc)
        assert exc.max_size_bytes == 5_000_000

    def test_is_attachments_service_error(self):
        assert isinstance(FileTooLargeError(1), AttachmentsServiceError)


@pytest.mark.unit
class TestDisallowedFileTypeError:
    def test_message_lists_allowed(self):
        exc = DisallowedFileTypeError(["pdf", "png"])
        assert "pdf" in str(exc)
        assert "png" in str(exc)
        assert exc.allowed == ["pdf", "png"]

    def test_empty_allowed_list(self):
        exc = DisallowedFileTypeError([])
        assert "Allowed types:" in str(exc)

    def test_is_attachments_service_error(self):
        assert isinstance(DisallowedFileTypeError([]), AttachmentsServiceError)


@pytest.mark.unit
class TestInvalidAttachmentValueError:
    def test_message_contains_field_name(self):
        exc = InvalidAttachmentValueError("receipt")
        assert "receipt" in str(exc)
        assert exc.field_name == "receipt"

    def test_is_attachments_service_error(self):
        assert isinstance(InvalidAttachmentValueError("f"), AttachmentsServiceError)


@pytest.mark.unit
class TestAttachmentNotFoundError:
    def test_message_contains_field_name(self):
        exc = AttachmentNotFoundError("invoice")
        assert "invoice" in str(exc)
        assert exc.field_name == "invoice"
        assert exc.reason is None

    def test_reason_is_appended_to_message(self):
        exc = AttachmentNotFoundError("invoice", reason="missing")
        assert "invoice" in str(exc)
        assert "Reason: missing" in str(exc)
        assert exc.reason == "missing"

    def test_is_attachments_service_error(self):
        assert isinstance(AttachmentNotFoundError("f"), AttachmentsServiceError)


@pytest.mark.unit
class TestAttachmentContextMismatchError:
    def _make(self, **overrides) -> AttachmentContextMismatchError:
        defaults = dict(
            attachment_id="att_abc",
            expected_field="receipt",
            actual_field="invoice",
            expected_property="prop_1",
            actual_property="prop_2",
            expected_policy="erasure",
            actual_policy="access",
        )
        return AttachmentContextMismatchError(**{**defaults, **overrides})

    def test_attributes_stored(self):
        exc = self._make()
        assert exc.attachment_id == "att_abc"
        assert exc.expected_field == "receipt"
        assert exc.actual_field == "invoice"
        assert exc.expected_property == "prop_1"
        assert exc.actual_property == "prop_2"
        assert exc.expected_policy == "erasure"
        assert exc.actual_policy == "access"

    def test_message_contains_key_fields(self):
        exc = self._make()
        msg = str(exc)
        assert "att_abc" in msg
        assert "receipt" in msg
        assert "invoice" in msg
        assert "prop_1" in msg
        assert "prop_2" in msg
        assert "erasure" in msg
        assert "access" in msg

    def test_is_attachments_service_error(self):
        assert isinstance(self._make(), AttachmentsServiceError)
