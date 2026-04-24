"""Save-time validation of ``display_condition`` rules attached to
``custom_privacy_request_fields``.

:class:`DisplayConditionValidator` runs structural + semantic checks when
a Privacy Center config is saved
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    Iterator,
    Optional,
    Set,
)

from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)

if TYPE_CHECKING:
    from fides.api.schemas.privacy_center_config import BaseCustomPrivacyRequestField


def _iter_leaves(condition: Condition) -> Iterator[ConditionLeaf]:
    """Walk a Condition tree and yield every ConditionLeaf."""
    if isinstance(condition, ConditionLeaf):
        yield condition
        return
    if isinstance(condition, ConditionGroup):
        for inner in condition.conditions:
            yield from _iter_leaves(inner)


def _iter_group_operators(condition: Condition) -> Iterator[GroupOperator]:
    """Walk a Condition tree and yield every group operator encountered."""
    if isinstance(condition, ConditionGroup):
        yield condition.logical_operator
        for inner in condition.conditions:
            yield from _iter_group_operators(inner)


class DisplayConditionValidator:
    """Save-time checker for ``display_condition`` rules attached to a
    single action's ``custom_privacy_request_fields``.

    Instantiate with the fields map, then call :meth:`validate` to run
    structural + semantic checks. Raises ``ValueError`` on first failure;
    callers translate to 422 in HTTP contexts.
    """

    ALLOWED_DISPLAY_OPERATORS: ClassVar[Set[Operator]] = {
        Operator.eq,
        Operator.neq,
        Operator.exists,
        Operator.not_exists,
        Operator.list_contains,
    }

    OPERATORS_BY_TARGET_TYPE: ClassVar[Dict[str, Set[Operator]]] = {
        "text": {Operator.eq, Operator.neq, Operator.exists, Operator.not_exists},
        "textarea": {Operator.eq, Operator.neq, Operator.exists, Operator.not_exists},
        "select": {Operator.eq, Operator.neq, Operator.exists, Operator.not_exists},
        "location": {Operator.eq, Operator.neq, Operator.exists, Operator.not_exists},
        "checkbox": {Operator.eq, Operator.neq, Operator.exists},
        "checkbox_group": {
            Operator.list_contains,
            Operator.exists,
            Operator.not_exists,
        },
        "multiselect": {
            Operator.list_contains,
            Operator.exists,
            Operator.not_exists,
        },
        "file": {Operator.exists, Operator.not_exists},
    }

    VALUELESS_OPERATORS: ClassVar[Set[Operator]] = {
        Operator.exists,
        Operator.not_exists,
    }

    def __init__(self, fields: Dict[str, "BaseCustomPrivacyRequestField"]) -> None:
        self.fields = fields

    def validate(self) -> None:
        for field_key, field in self.fields.items():
            condition = getattr(field, "display_condition", None)
            if condition is None:
                continue

            for group_op in _iter_group_operators(condition):
                if group_op not in (GroupOperator.and_, GroupOperator.or_):
                    raise ValueError(f"'{field_key}': unsupported group operator")

            for leaf in _iter_leaves(condition):
                self._validate_leaf(field_key, leaf)

    def _validate_leaf(self, field_key: str, leaf: ConditionLeaf) -> None:
        if leaf.operator not in self.ALLOWED_DISPLAY_OPERATORS:
            raise ValueError(
                f"'{field_key}': unsupported operator '{leaf.operator.value}'"
            )

        referenced = leaf.field_address
        if referenced not in self.fields:
            raise ValueError(f"'{field_key}': references unknown field '{referenced}'")

        target_type = getattr(self.fields[referenced], "field_type", None)

        if target_type is not None:
            allowed = self.OPERATORS_BY_TARGET_TYPE.get(target_type)
            if allowed is not None and leaf.operator not in allowed:
                raise ValueError(
                    f"'{field_key}': operator '{leaf.operator.value}' not allowed against '{referenced}' ({target_type})"
                )

        self._validate_value_for_target(field_key, leaf, target_type)

    def _validate_value_for_target(
        self,
        field_key: str,
        leaf: ConditionLeaf,
        target_type: Optional[str],
    ) -> None:
        """Reject leaf values whose type does not match the referenced field."""
        if leaf.operator in self.VALUELESS_OPERATORS:
            return

        value = leaf.value
        if value is None:
            raise ValueError(
                f"'{field_key}': missing value for operator '{leaf.operator.value}'"
            )

        if target_type == "checkbox":
            if not isinstance(value, bool):
                raise ValueError(
                    f"'{field_key}': checkbox '{leaf.field_address}' requires a bool value"
                )
            return

        if target_type in ("checkbox_group", "multiselect"):
            if isinstance(value, list):
                if not all(isinstance(v, str) for v in value):
                    raise ValueError(
                        f"'{field_key}': list value for '{leaf.field_address}' must contain only strings"
                    )
                return
            if isinstance(value, str):
                return
            raise ValueError(
                f"'{field_key}': '{leaf.field_address}' ({target_type}) requires a string or list of strings"
            )

        if target_type in ("text", "textarea", "select", "location") and not isinstance(
            value, str
        ):
            raise ValueError(
                f"'{field_key}': '{leaf.field_address}' ({target_type}) requires a string value"
            )
