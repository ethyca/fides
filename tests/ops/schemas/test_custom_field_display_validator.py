"""Tests for :class:`DisplayConditionValidator` — save-time structural +
semantic checks on ``display_condition`` entries.
"""

import pytest
from pydantic import ValidationError

from fides.api.schemas.custom_field_display_validator import (
    DisplayConditionValidator,
    _iter_leaves,
)
from fides.api.schemas.privacy_center_config import (
    ConsentConfigButton,
    CustomPrivacyRequestField,
    IdentityInputs,
    LocationCustomPrivacyRequestField,
    PartialPrivacyRequestOption,
    PrivacyRequestOption,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


def _leaf(field_address, operator, value=None):
    return ConditionLeaf(field_address=field_address, operator=operator, value=value)


def _fields(target, *, detail_condition=None, detail_field="detail"):
    base = dict(target)
    base[detail_field] = CustomPrivacyRequestField(
        label="Detail", field_type="textarea", display_condition=detail_condition
    )
    return base


def _target(key, field_type, **kwargs):
    cls = kwargs.pop("_cls", CustomPrivacyRequestField)
    return {
        key: cls(label="Target", field_type=field_type, **kwargs)
        if field_type
        else cls(label="Target", **kwargs)
    }


VALID_CASES = [
    pytest.param(
        {
            "a": CustomPrivacyRequestField(label="A", field_type="text"),
            "b": CustomPrivacyRequestField(label="B", field_type="checkbox"),
        },
        id="no_display_conditions",
    ),
    pytest.param(
        _fields(
            _target("reason", "select"),
            detail_condition=_leaf("reason", Operator.eq, "other"),
        ),
        id="select_target_string_value",
    ),
    pytest.param(
        _fields(
            _target("cats", "checkbox_group", options=["a", "b"]),
            detail_condition=_leaf("cats", Operator.list_contains, "a"),
        ),
        id="checkbox_group_string_value",
    ),
    pytest.param(
        _fields(
            _target("agree", "checkbox"),
            detail_condition=_leaf("agree", Operator.eq, True),
        ),
        id="checkbox_bool_value",
    ),
    pytest.param(
        _fields(
            _target("reason", "text"),
            detail_condition=_leaf("reason", Operator.exists),
        ),
        id="exists_needs_no_value",
    ),
    pytest.param(
        _fields(
            {"country": LocationCustomPrivacyRequestField(label="Country")},
            detail_condition=_leaf("country", Operator.eq, "US"),
        ),
        id="location_target_string_value",
    ),
    pytest.param(
        _fields(
            {"untyped": CustomPrivacyRequestField(label="Untyped")},
            # No field_type on target → operator + value-type checks skip.
            detail_condition=_leaf("untyped", Operator.eq, 123),
        ),
        id="target_without_field_type",
    ),
    pytest.param(
        _fields(
            _target("tags", "multiselect", options=["a", "b"]),
            detail_condition=_leaf("tags", Operator.list_contains, "a"),
        ),
        id="multiselect_list_contains",
    ),
    pytest.param(
        _fields(
            _target("cats", "checkbox_group", options=["a", "b"]),
            detail_condition=_leaf("cats", Operator.list_contains, ["a", "b"]),
        ),
        id="list_value_of_strings",
    ),
]


INVALID_CASES = [
    pytest.param(
        {
            "detail": CustomPrivacyRequestField(
                label="Detail",
                field_type="textarea",
                display_condition=_leaf("reason", Operator.eq, "other"),
            ),
        },
        "references unknown field 'reason'",
        id="references_unknown_field",
    ),
    pytest.param(
        _fields(
            _target("a", "text"),
            detail_condition=_leaf("a", Operator.contains, "x"),
        ),
        "unsupported operator 'contains'",
        id="disallowed_operator",
    ),
    pytest.param(
        _fields(
            _target("agree", "checkbox"),
            detail_condition=_leaf("agree", Operator.list_contains, "x"),
        ),
        "operator 'list_contains' not allowed against 'agree' \\(checkbox\\)",
        id="operator_target_mismatch",
    ),
    pytest.param(
        _fields(
            _target("agree", "checkbox"),
            detail_condition=_leaf("agree", Operator.eq, "true"),
        ),
        "checkbox 'agree' requires a bool value",
        id="checkbox_requires_bool",
    ),
    pytest.param(
        _fields(
            _target("reason", "text"),
            detail_condition=_leaf("reason", Operator.eq, 42),
        ),
        "'reason' \\(text\\) requires a string value",
        id="text_target_non_string",
    ),
    pytest.param(
        _fields(
            _target("reason", "text"),
            detail_condition=_leaf("reason", Operator.eq),
        ),
        "missing value for operator 'eq'",
        id="eq_without_value",
    ),
    pytest.param(
        _fields(
            _target("agree", "checkbox"),
            detail_condition=ConditionGroup(
                logical_operator=GroupOperator.and_,
                conditions=[
                    _leaf("agree", Operator.eq, True),
                    _leaf("missing", Operator.exists),  # bad leaf
                ],
            ),
        ),
        "references unknown field 'missing'",
        id="group_condition_bad_leaf",
    ),
    pytest.param(
        _fields(
            _target("cats", "checkbox_group", options=["a", "b"]),
            detail_condition=_leaf("cats", Operator.list_contains, [1, 2]),
        ),
        "list value for 'cats' must contain only strings",
        id="list_value_with_non_string",
    ),
    pytest.param(
        _fields(
            _target("cats", "checkbox_group", options=["a", "b"]),
            detail_condition=_leaf("cats", Operator.list_contains, 42),
        ),
        "'cats' \\(checkbox_group\\) requires a string or list of strings",
        id="checkbox_group_non_string_non_list",
    ),
    pytest.param(
        _fields(
            _target("agree", "checkbox"),
            detail_condition=ConditionGroup.model_construct(
                logical_operator="xor",
                conditions=[_leaf("agree", Operator.exists)],
            ),
        ),
        "unsupported group operator",
        id="unknown_group_operator",
    ),
]


class TestValidateDisplayConditions:
    @pytest.mark.parametrize("fields", VALID_CASES)
    def test_valid(self, fields):
        DisplayConditionValidator(fields).validate()

    @pytest.mark.parametrize("fields, match", INVALID_CASES)
    def test_invalid(self, fields, match):
        with pytest.raises(ValueError, match=match):
            DisplayConditionValidator(fields).validate()


class TestIterLeavesEdgeCases:
    def test_non_condition_input_yields_nothing(self):
        assert list(_iter_leaves("not a condition")) == []  # type: ignore[arg-type]

    def test_empty_group_yields_nothing(self):
        empty = ConditionGroup.model_construct(
            logical_operator=GroupOperator.and_, conditions=[]
        )
        assert list(_iter_leaves(empty)) == []


_VALID_FIELDS = _fields(
    _target("reason", "select"),
    detail_condition=_leaf("reason", Operator.eq, "other"),
)
_INVALID_FIELDS = {
    "orphan": CustomPrivacyRequestField(
        label="Orphan",
        field_type="textarea",
        display_condition=_leaf("does_not_exist", Operator.eq, "x"),
    ),
}


def _pro(fields):
    return PrivacyRequestOption(
        policy_key="k",
        icon_path="/x",
        title="t",
        description="d",
        custom_privacy_request_fields=fields,
    )


def _ccb(fields):
    return ConsentConfigButton(
        description="d",
        icon_path="/x",
        identity_inputs=IdentityInputs(email="required"),
        title="t",
        custom_privacy_request_fields=fields,
    )


def _partial(fields):
    return PartialPrivacyRequestOption(
        policy_key="k", title="t", custom_privacy_request_fields=fields
    )


@pytest.fixture(
    params=[_pro, _ccb, _partial],
    ids=["PrivacyRequestOption", "ConsentConfigButton", "PartialPrivacyRequestOption"],
)
def builder(request):
    return request.param


class TestDisplayConditionMixinWiring:
    def test_mixin_accepts_valid_fields(self, builder):
        assert builder(_VALID_FIELDS).custom_privacy_request_fields is not None

    def test_mixin_rejects_invalid_fields(self, builder):
        with pytest.raises(ValidationError, match="references unknown field"):
            builder(_INVALID_FIELDS)

    def test_mixin_skips_when_fields_absent(self, builder):
        assert builder(None).custom_privacy_request_fields is None
