"""Tests for PrivacyRequestAttachment response schema."""

import pytest
from pydantic import ValidationError

from fides.api.schemas.attachment import PrivacyRequestAttachment


class TestPrivacyRequestAttachment:
    def test_accepts_id(self):
        assert PrivacyRequestAttachment(id="att_123").id == "att_123"

    def test_rejects_missing_id(self):
        with pytest.raises(ValidationError):
            PrivacyRequestAttachment()

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            PrivacyRequestAttachment(id="att_123", extra="nope")
