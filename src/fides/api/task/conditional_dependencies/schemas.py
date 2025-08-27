from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, model_validator


class Operator(str, Enum):
    # Basic comparison operators
    # Column value equals user input (e.g., user.role eq "admin")
    eq = "eq"
    # Column value not equal to user input (e.g., user.status neq "inactive")
    neq = "neq"

    # Numeric comparison operators
    # Column value less than user input (e.g., user.age lt 18)
    lt = "lt"
    # Column value less than or equal to user input (e.g., user.score lte 100)
    lte = "lte"
    # Column value greater than user input (e.g., user.balance gt 1000)
    gt = "gt"
    # Column value greater than or equal to user input (e.g., user.rating gte 4.0)
    gte = "gte"

    # Existence operators
    # Field exists and is not None (e.g., user.email exists)
    exists = "exists"
    # Field does not exist or is None (e.g., user.middle_name not_exists)
    not_exists = "not_exists"

    # List membership operators (work with both single values and lists)
    #
    # Column value is in user's list OR user's value is in column's list
    list_contains = "list_contains"
    # Examples: user.role list_contains ["admin", "moderator"] (role in list)
    #          user.permissions list_contains "write" (value in permissions)

    # Column value is NOT in user's list OR user's value is NOT in column's list
    not_in_list = "not_in_list"
    # Examples: user.role not_in_list ["banned", "suspended"] (role not blocked)
    #          user.permissions not_in_list "delete" (value not in permissions)

    # List-to-list comparison operators (both values must be lists)
    # Lists have at least one common element
    list_intersects = "list_intersects"
    # Example: user.roles list_intersects ["admin", "moderator"] (any common role)

    # Column list is completely contained within user's list
    list_subset = "list_subset"
    # Example: user.permissions list_subset ["read", "write", "delete", "manage"]
    #         (all user permissions are allowed)

    # Column list completely contains user's list
    list_superset = "list_superset"
    # Example: user.tags list_superset ["premium", "verified"]
    #         (user has all required tags plus extras)

    # Lists have no common elements
    list_disjoint = "list_disjoint"
    # Example: user.roles list_disjoint ["banned", "suspended"]
    #         (user has no restricted roles)

    # String operators
    # String starts with user input (e.g., user.email starts_with "admin@")
    starts_with = "starts_with"
    # String ends with user input (e.g., user.domain ends_with ".com")
    ends_with = "ends_with"
    # String contains user input (e.g., user.description contains "verified")
    contains = "contains"


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


# Evaluation result for a single condition
class ConditionEvaluationResult(BaseModel):
    field_address: str
    operator: Operator
    expected_value: Optional[
        Union[str, int, float, bool, List[Union[str, int, float, bool]]]
    ]
    actual_value: Any
    result: bool
    message: str


# Evaluation result for a group of conditions
class GroupEvaluationResult(BaseModel):
    logical_operator: GroupOperator
    condition_results: list["EvaluationResult"]
    result: bool


# Union type for evaluation results
EvaluationResult = Union[ConditionEvaluationResult, GroupEvaluationResult]


# Use model_rebuild to allow recursive nesting
Condition = Union[ConditionLeaf, ConditionGroup]
ConditionGroup.model_rebuild()
GroupEvaluationResult.model_rebuild()
