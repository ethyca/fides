from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator


class Operator(str, Enum):
    eq = "eq"
    neq = "neq"
    lt = "lt"
    lte = "lte"
    gt = "gt"
    gte = "gte"
    exists = "exists"
    not_exists = "not_exists"
    list_contains = "list_contains"
    not_in_list = "not_in_list"


class GroupOperator(str, Enum):
    and_ = "and"
    or_ = "or"


# Leaf condition (e.g., "user.name exists", "user.created_at >= 2024-01-01")
class ConditionLeaf(BaseModel):
    field_address: str = Field(
        description="Field path to check (e.g., 'user.name', 'billing.subscription.status')"
    )
    operator: Operator = Field(description="Operator to apply")
    value: Optional[
        Union[str, int, float, bool, List[Union[str, int, float, bool]]]
    ] = Field(default=None, description="Expected value for comparison")


# Nested logical condition (AND, OR)
class ConditionGroup(BaseModel):
    logical_operator: GroupOperator = Field(
        description="Logical operator: 'and' or 'or'"
    )
    conditions: list["Condition"] = Field(
        description="List of conditions or nested groups"
    )

    @model_validator(mode="after")
    def validate_conditions(self) -> "ConditionGroup":
        if not self.conditions:
            raise ValueError("conditions list cannot be empty")
        return self


# Use model_rebuild to allow recursive nesting
Condition = Union[ConditionLeaf, ConditionGroup]
ConditionGroup.model_rebuild()
