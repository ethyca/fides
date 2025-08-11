from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator


class Operator(str, Enum):
    # Basic comparison operators
    eq = "eq"  # Column value equals user input (e.g., user.role eq "admin")
    neq = (
        "neq"  # Column value not equal to user input (e.g., user.status neq "inactive")
    )

    # Numeric comparison operators
    lt = "lt"  # Column value less than user input (e.g., user.age lt 18)
    lte = "lte"  # Column value less than or equal to user input (e.g., user.score lte 100)
    gt = "gt"  # Column value greater than user input (e.g., user.balance gt 1000)
    gte = "gte"  # Column value greater than or equal to user input (e.g., user.rating gte 4.0)

    # Existence operators
    exists = "exists"  # Field exists and is not None (e.g., user.email exists)
    not_exists = "not_exists"  # Field does not exist or is None (e.g., user.middle_name not_exists)

    # List membership operators (work with both single values and lists)
    list_contains = "list_contains"  # Column value is in user's list OR user's value is in column's list
    # Examples: user.role list_contains ["admin", "moderator"] (role in list)
    #          user.permissions list_contains "write" (value in permissions)

    not_in_list = "not_in_list"  # Column value is NOT in user's list OR user's value is NOT in column's list
    # Examples: user.role not_in_list ["banned", "suspended"] (role not blocked)
    #          user.permissions not_in_list "delete" (value not in permissions)

    # List-to-list comparison operators (both values must be lists)
    list_intersects = "list_intersects"  # Lists have at least one common element
    # Example: user.roles list_intersects ["admin", "moderator"] (any common role)

    list_subset = (
        "list_subset"  # Column list is completely contained within user's list
    )
    # Example: user.permissions list_subset ["read", "write", "delete", "manage"]
    #         (all user permissions are allowed)

    list_superset = "list_superset"  # Column list completely contains user's list
    # Example: user.tags list_superset ["premium", "verified"]
    #         (user has all required tags plus extras)

    list_disjoint = "list_disjoint"  # Lists have no common elements
    # Example: user.roles list_disjoint ["banned", "suspended"]
    #         (user has no restricted roles)

    # String operators
    starts_with = "starts_with"  # String starts with user input (e.g., user.email starts_with "admin@")
    ends_with = (
        "ends_with"  # String ends with user input (e.g., user.domain ends_with ".com")
    )
    contains = "contains"  # String contains user input (e.g., user.description contains "verified")


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
