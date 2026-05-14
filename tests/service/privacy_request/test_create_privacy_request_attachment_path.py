"""Unit tests targeting the attachment-hook wiring inside ``create_privacy_request``."""

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.privacy_center_config import (
    CustomPrivacyRequestField,
    LocationCustomPrivacyRequestField,
)
from tests.service.privacy_request._helpers import _make_action, _req, _svc


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
class TestCreatePrivacyRequestPromotionFailure:
    """Rollback path when ``_promote_attachment_state`` raises (unit, mocked).

    The integration-marked twins in ``test_privacy_request_service.py`` verify
    the same contract end-to-end against Postgres; these unit tests keep the
    branches in the Codecov-tracked unit coverage."""

    def _patches(self, svc, req, fake_pr, fake_policy):
        return [
            patch.object(
                svc, "_resolve_action_for_request", return_value=_make_action(None)
            ),
            patch.object(
                svc, "_resolve_attachment_state", return_value=(req, "ATTACH_STATE")
            ),
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
        ]

    def _build(self):
        svc = _svc()
        req = _req(location="US-CA")
        fake_policy = MagicMock()
        fake_policy.id = "pol_1"
        fake_policy.generate_masking_secrets.return_value = []
        fake_pr = MagicMock()
        fake_pr.id = "pr_1"
        return svc, req, fake_pr, fake_policy

    def _run_with_failing_promote(self, promote_exc):
        svc, req, fake_pr, fake_policy = self._build()
        with ExitStack() as stack:
            for cm in self._patches(svc, req, fake_pr, fake_policy):
                stack.enter_context(cm)
            stack.enter_context(
                patch.object(svc, "_promote_attachment_state", side_effect=promote_exc)
            )
            with pytest.raises(PrivacyRequestError) as exc_info:
                svc.create_privacy_request(req, authenticated=True)
        return svc, fake_pr, exc_info.value

    def test_promotion_failure_deletes_request_and_wraps_with_generic_message(self):
        # Leaky detail must survive on ``__cause__`` but not in the user message.
        leaky = "privacy_request_attachments/secret_path.pdf"
        svc, fake_pr, exc = self._run_with_failing_promote(RuntimeError(leaky))

        assert "Attachment processing failed" in str(exc)
        assert leaky not in str(exc)
        assert isinstance(exc.__cause__, RuntimeError)
        assert leaky in str(exc.__cause__)
        fake_pr.delete.assert_called_once_with(svc.db)

    def test_delete_failure_still_surfaces_promotion_error(self):
        svc, req, fake_pr, fake_policy = self._build()
        fake_pr.delete.side_effect = RuntimeError("delete blew up")
        with ExitStack() as stack:
            for cm in self._patches(svc, req, fake_pr, fake_policy):
                stack.enter_context(cm)
            stack.enter_context(
                patch.object(
                    svc,
                    "_promote_attachment_state",
                    side_effect=RuntimeError("promotion blew up"),
                )
            )
            with pytest.raises(PrivacyRequestError) as exc_info:
                svc.create_privacy_request(req, authenticated=True)

        # ``__cause__`` is the *promotion* exception, not the delete one —
        # delete failure is logged and swallowed.
        assert "promotion blew up" in str(exc_info.value.__cause__)
        assert "delete blew up" not in str(exc_info.value)

    def test_privacy_request_error_from_hook_is_not_double_rewrapped(self):
        _, _, exc = self._run_with_failing_promote(
            PrivacyRequestError("Hook-specific detail", {"k": "v"})
        )
        # Promotion branch wraps once with the generic message; the outer
        # catch-all must NOT then re-wrap it with "This record could not be added".
        assert "Attachment processing failed" in str(exc)
        assert "This record could not be added" not in str(exc)


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
