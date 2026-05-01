"""Tests for :func:`evaluate_submission` — submission-time visibility
check on ``custom_privacy_request_fields``."""

import pytest

from fides.api.schemas.privacy_center_config import CustomPrivacyRequestField
from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField as SubmittedField,
)
from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator
from fides.api.task.conditional_dependencies.schemas import ConditionLeaf, Operator
from fides.service.privacy_request.custom_field_display_evaluator import (
    DisplayConditionViolation,
    _submitted_has_value,
    evaluate_submission,
)


def _leaf(field_address, operator, value=None):
    return ConditionLeaf(field_address=field_address, operator=operator, value=value)


def _cprf(label, **kw):
    return CustomPrivacyRequestField(label=label, **kw)


def _sv(value, label="x"):
    """Build a submitted ``CustomPrivacyRequestField`` (runtime model with
    ``.value``) — what callers actually pass to ``evaluate_submission``.
    """
    return SubmittedField(label=label, value=value)


def _agree_detail(detail_condition=None, *, agree_kw=None, detail_kw=None):
    """checkbox ``agree`` + textarea ``detail`` (both ``required=False`` by
    default to keep tests focused on visibility, not the required-check)."""
    agree = {"field_type": "checkbox", "required": False, **(agree_kw or {})}
    detail = {
        "field_type": "textarea",
        "required": False,
        "display_condition": detail_condition,
        **(detail_kw or {}),
    }
    return {"agree": _cprf("Agree", **agree), "detail": _cprf("Detail", **detail)}


@pytest.fixture
def evaluator():
    return ConditionEvaluator(None)


_AGREE_TRUE = _leaf("agree", Operator.eq, True)


class TestEvaluateSubmission:
    @pytest.mark.parametrize(
        "fields, submitted",
        [
            pytest.param(
                {
                    "a": _cprf("A", field_type="text", required=False),
                    "b": _cprf("B", field_type="checkbox", required=False),
                },
                {},
                id="no_conditions",
            ),
            pytest.param(
                _agree_detail(_AGREE_TRUE),
                {"agree": _sv(True), "detail": _sv("text")},
                id="condition_true",
            ),
            pytest.param(
                _agree_detail(_AGREE_TRUE),
                {"agree": _sv(False)},
                id="condition_false_nothing_submitted",
            ),
            pytest.param(
                _agree_detail(_leaf("agree", Operator.exists)),
                {},
                id="exists_with_no_submission",
            ),
        ],
    )
    def test_valid_submissions_pass(self, evaluator, fields, submitted):
        evaluate_submission(fields, submitted, evaluator)

    def test_gated_off_submission_raises(self, evaluator):
        # detail's condition is false (agree=False) but a value was submitted.
        with pytest.raises(DisplayConditionViolation, match="'detail' is gated off"):
            evaluate_submission(
                _agree_detail(_AGREE_TRUE),
                {"agree": _sv(False), "detail": _sv("x")},
                evaluator,
            )

    def test_required_applicable_missing_raises(self, evaluator):
        fields = {"reason": _cprf("Reason", field_type="text", required=True)}
        with pytest.raises(DisplayConditionViolation, match="Required field 'reason'"):
            evaluate_submission(fields, {}, evaluator)

    def test_required_non_applicable_passes(self, evaluator):
        # required=True is ignored when the field is not applicable.
        fields = _agree_detail(_AGREE_TRUE, detail_kw={"required": True})
        evaluate_submission(fields, {"agree": _sv(False)}, evaluator)

    def test_unknown_submitted_key_ignored(self, evaluator):
        fields = {"agree": _cprf("Agree", field_type="checkbox", required=False)}
        evaluate_submission(fields, {"stray": _sv("x")}, evaluator)

    def test_transitive_hide_through_fixed_point(self, evaluator):
        # b depends on a; c depends on b. Hiding a cascades to c.
        fields = {
            "a": _cprf("A", field_type="checkbox"),
            "b": _cprf(
                "B", field_type="text", display_condition=_leaf("a", Operator.eq, True)
            ),
            "c": _cprf(
                "C", field_type="text", display_condition=_leaf("b", Operator.exists)
            ),
        }
        with pytest.raises(DisplayConditionViolation, match="'b' is gated off"):
            evaluate_submission(
                fields,
                {"a": _sv(False), "b": _sv("x"), "c": _sv("y")},
                evaluator,
            )

    def test_evaluator_exception_hides_field(self, evaluator, monkeypatch):
        # Defensive: evaluator blowup hides the field; submitting it then raises.
        def boom(*a, **kw):
            raise RuntimeError("evaluator exploded")

        monkeypatch.setattr(evaluator, "evaluate_rule", boom)
        with pytest.raises(DisplayConditionViolation, match="'detail' is gated off"):
            evaluate_submission(
                _agree_detail(_AGREE_TRUE),
                {"agree": _sv(True), "detail": _sv("text")},
                evaluator,
            )


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", False),
        (None, False),
        ([], False),
        ("x", True),
        (0, True),
        (False, True),
        ({"label": "x", "value": None}, False),
        ({"label": "x", "value": "y"}, True),
    ],
)
def test_submitted_has_value(raw, expected):
    assert _submitted_has_value(raw) is expected
