"""Tests for pre-approval webhook header changes.

Covers:
- New reply-to-eligible and reply-to-not-eligible headers are sent
- Deprecated reply-to-approve and reply-to-deny headers are still sent
- Both new and old headers point to the same URLs
- reply-to-token is still included
"""

import pytest
import requests_mock

from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.schemas.redis_cache import Identity


class TestPreApprovalWebhookHeaders:
    """Verify that trigger_pre_approval_webhook sends both new and deprecated headers."""

    def test_webhook_sends_new_and_deprecated_headers(
        self,
        db,
        privacy_request_status_pending,
        https_connection_config,
        pre_approval_webhooks,
    ):
        webhook = pre_approval_webhooks[0]
        identity = Identity(email="customer-1@example.com")
        privacy_request_status_pending.cache_identity(identity)

        captured_headers = {}

        def capture_headers(request, context):
            captured_headers.update(dict(request.headers))
            context.status_code = 200
            return "{}"

        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                https_connection_config.secrets["url"],
                json=capture_headers,
            )
            privacy_request_status_pending.trigger_pre_approval_webhook(webhook)

        pr_id = privacy_request_status_pending.id

        # New headers are present
        assert "reply-to-eligible" in captured_headers
        assert "reply-to-not-eligible" in captured_headers

        # Deprecated headers are still present
        assert "reply-to-approve" in captured_headers
        assert "reply-to-deny" in captured_headers

        # Auth token is present
        assert "reply-to-token" in captured_headers

        # New and deprecated point to the same URLs
        assert (
            captured_headers["reply-to-eligible"]
            == captured_headers["reply-to-approve"]
        )
        assert (
            captured_headers["reply-to-not-eligible"]
            == captured_headers["reply-to-deny"]
        )

        # URLs contain the correct privacy request id and paths
        assert (
            f"/privacy-request/{pr_id}/pre-approve/eligible"
            == captured_headers["reply-to-eligible"]
        )
        assert (
            f"/privacy-request/{pr_id}/pre-approve/not-eligible"
            == captured_headers["reply-to-not-eligible"]
        )
