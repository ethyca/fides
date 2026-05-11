"""Unit tests for legacy DSR Redis key discovery helpers.

Location: ``tests/lethe/unit/migration/``. Marker: ``@pytest.mark.unit``.
"""

import pytest

from lethe.migration.redis_reader import extract_privacy_request_id_from_key

pytestmark = pytest.mark.unit


def test_extract_privacy_request_id_from_dsr_prefix() -> None:
    pr_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert extract_privacy_request_id_from_key(f"dsr:{pr_id}:drp:meta") == pr_id


def test_extract_privacy_request_id_from_legacy_id_prefix() -> None:
    pr_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert extract_privacy_request_id_from_key(f"id-{pr_id}-identity-email") == pr_id


def test_extract_privacy_request_id_unknown_key() -> None:
    assert extract_privacy_request_id_from_key("unrelated:key") is None
