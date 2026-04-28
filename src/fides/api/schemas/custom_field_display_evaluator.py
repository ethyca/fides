"""Submission-time evaluation of ``display_condition`` rules attached to
``custom_privacy_request_fields``. One public entry point —
:func:`evaluate_submission` — resolves which fields are applicable given
the submission and raises :class:`DisplayConditionViolation` on the first
contract violation. Callers translate the exception to whatever type
their layer expects (HTTP error, ``PrivacyRequestError``, etc.).
"""

from typing import Any

from fides.api.schemas.privacy_center_field_base import BaseCustomPrivacyRequestField
from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator


class DisplayConditionViolation(ValueError):
    """A submission violates the display_condition contract — either a
    gated-off field was submitted or a required-applicable field is missing.
    """


def evaluate_submission(
    fields: dict[str, BaseCustomPrivacyRequestField],
    submitted: dict[str, Any],
    condition_evaluator: ConditionEvaluator,
) -> None:
    """Resolve which fields are applicable given ``submitted`` and raise
    :class:`DisplayConditionViolation` on the first contract breach:

    * a field gated off by its ``display_condition`` must not be submitted;
    * a required field that is applicable must have a value.

    ``submitted`` may hold raw JSON dicts, ``CustomPrivacyRequestField``
    Pydantic instances, or bare values — :func:`_extract_submitted_value`
    normalises all three.
    """
    applicable = _resolve_applicable(fields, submitted, condition_evaluator)
    _enforce_visibility(fields, submitted, applicable)


def _resolve_applicable(
    fields: dict[str, BaseCustomPrivacyRequestField],
    submitted_values: dict[str, Any],
    evaluator: ConditionEvaluator,
) -> set[str]:
    """Fixed-point: keep filtering until the applicable set stops shrinking."""
    normalised = {k: _extract_submitted_value(v) for k, v in submitted_values.items()}
    applicable: set[str] = set(fields.keys())
    previous: set[str] = set()
    while previous != applicable:
        previous = applicable
        data_view = {k: normalised.get(k) for k in applicable}
        applicable = {
            k for k in applicable if _is_applicable(fields[k], data_view, evaluator)
        }
    return applicable


def _enforce_visibility(
    fields: dict[str, BaseCustomPrivacyRequestField],
    submitted_values: dict[str, Any],
    applicable: set[str],
) -> None:
    """Reject gated-off submissions + missing required-applicable values."""
    for key, raw in submitted_values.items():
        if key in fields and key not in applicable and _submitted_has_value(raw):
            raise DisplayConditionViolation(
                f"Field '{key}' is gated off by its display_condition and "
                "must not be submitted"
            )
    for key, field in fields.items():
        if (
            key in applicable
            and bool(field.required)
            and not _submitted_has_value(submitted_values.get(key))
        ):
            raise DisplayConditionViolation(f"Required field '{key}' is missing")


def _is_applicable(
    field: BaseCustomPrivacyRequestField,
    data_view: dict[str, Any],
    evaluator: ConditionEvaluator,
) -> bool:
    """True if ``field`` has no display_condition or it evaluates true.
    Evaluator errors → hide the field (can't prove applicability)."""
    condition = field.display_condition
    if condition is None:
        return True
    try:
        return bool(evaluator.evaluate_rule(condition, data_view).result)
    except Exception:  # pylint: disable=broad-except
        return False


def _extract_submitted_value(raw: Any) -> Any:
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"]
    if hasattr(raw, "value"):
        return raw.value
    return raw


def _submitted_has_value(raw: Any) -> bool:
    value = _extract_submitted_value(raw)
    if value is None:
        return False
    if isinstance(value, str) and value == "":
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    return True
