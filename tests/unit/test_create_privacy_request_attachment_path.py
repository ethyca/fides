"""Unit tests targeting the attachment-hook wiring inside ``create_privacy_request``."""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.privacy_center_config import (
    CustomPrivacyRequestField,
    LocationCustomPrivacyRequestField,
)
from fides.api.schemas.privacy_request import PrivacyRequestCreate
from fides.api.schemas.redis_cache import Identity
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService


def _make_action(custom_fields):
    a = MagicMock()
    a.custom_privacy_request_fields = custom_fields
    return a


def _svc() -> PrivacyRequestService:
    return PrivacyRequestService(MagicMock(), MagicMock(), MagicMock())


def _req(**kw) -> PrivacyRequestCreate:
    return PrivacyRequestCreate(
        identity=Identity(email="jane@example.com"),
        policy_key="default_access_policy",
        **kw,
    )


@pytest.mark.unit
class TestAttachmentHookDefaults:
    @pytest.mark.parametrize("action", [None, _make_action(None)])
    def test_resolve_default_returns_input_and_none_state(self, action):
        req = _req()
        out_req, state = _svc()._resolve_attachment_state(req, action)
        assert out_req is req
        assert state is None

    @pytest.mark.parametrize("state", [None, {"opaque": "object"}])
    def test_promote_default_is_noop(self, state):
        assert _svc()._promote_attachment_state(MagicMock(), state) is None


@pytest.mark.unit
class TestCreatePrivacyRequestAttachmentWiring:
    def test_resolve_hook_called_with_resolved_action(self):
        svc = _svc()
        req = _req(location="US-CA")
        req.policy_key = "missing-policy"
        action_sentinel = _make_action(None)
        with (
            patch.object(
                svc, "_resolve_action_for_request", return_value=action_sentinel
            ),
            patch.object(
                svc, "_resolve_attachment_state", return_value=(req, "S")
            ) as resolve,
            patch(
                "fides.service.privacy_request.privacy_request_service.Policy.get_by",
                return_value=None,
            ),
            pytest.raises(PrivacyRequestError, match="does not exist"),
        ):
            svc.create_privacy_request(req, authenticated=True)
        resolve.assert_called_once_with(req, action_sentinel)

    def test_promote_hook_invoked_on_success_path(self):
        svc = _svc()
        req = _req(location="US-CA")
        action_sentinel = _make_action(None)
        fake_policy = MagicMock()
        fake_policy.id = "pol_1"
        fake_policy.generate_masking_secrets.return_value = []
        fake_pr = MagicMock()
        fake_pr.id = "pr_1"

        with (
            patch.object(
                svc, "_resolve_action_for_request", return_value=action_sentinel
            ),
            patch.object(
                svc, "_resolve_attachment_state", return_value=(req, "ATTACH_STATE")
            ),
            patch.object(svc, "_promote_attachment_state") as promote,
            patch(
                "fides.service.privacy_request.privacy_request_service.Policy.get_by",
                return_value=fake_policy,
            ),
            patch(
                "fides.service.privacy_request.privacy_request_service.build_required_privacy_request_kwargs",
                return_value={},
            ),
            patch(
                "fides.service.privacy_request.privacy_request_service.PrivacyRequest.create",
                return_value=fake_pr,
            ),
            patch(
                "fides.service.privacy_request.privacy_request_service._create_or_update_custom_fields"
            ),
            patch("fides.service.privacy_request.privacy_request_service.cache_data"),
            patch(
                "fides.service.privacy_request.privacy_request_service.check_and_dispatch_error_notifications"
            ),
            patch(
                "fides.service.privacy_request.privacy_request_service._handle_notifications_and_processing"
            ),
            patch(
                "fides.service.privacy_request.privacy_request_service.check_for_duplicates"
            ),
        ):
            result = svc.create_privacy_request(req, authenticated=True)

        assert result is fake_pr
        promote.assert_called_once_with(fake_pr, "ATTACH_STATE")


@pytest.mark.unit
class TestValidatorActionWiring:
    def test_validate_required_location_fields_short_circuits_on_none(self):
        _svc()._validate_required_location_fields(_req(), None)

    def test_validate_required_location_fields_short_circuits_on_no_custom_fields(
        self,
    ):
        _svc()._validate_required_location_fields(_req(), _make_action(None))

    def test_validate_field_visibility_short_circuits_on_none(self):
        _svc()._validate_field_visibility(_req(), None)

    def test_validate_field_visibility_short_circuits_on_no_custom_fields(self):
        _svc()._validate_field_visibility(_req(), _make_action(None))

    def test_validate_field_visibility_ignores_location_only_action(self):
        action = _make_action(
            {"country": LocationCustomPrivacyRequestField(label="Country")}
        )
        _svc()._validate_field_visibility(_req(), action)

    def test_validate_field_visibility_raises_when_required_text_missing(self):
        svc = _svc()
        action = _make_action(
            {
                "reason": CustomPrivacyRequestField(
                    label="Reason", field_type="text", required=True
                )
            }
        )
        with pytest.raises(
            PrivacyRequestError, match="Required field 'reason' is missing"
        ):
            svc._validate_field_visibility(_req(), action)
