import numbers
import operator as py_operator

from fides.api.task.conditional_dependencies.schemas import Operator

# Define operator methods for validation
operator_methods = {
    Operator.exists: lambda a, _: a is not None,
    Operator.not_exists: lambda a, _: a is None,
    Operator.eq: py_operator.eq,
    Operator.neq: py_operator.ne,
    Operator.lt: lambda a, b: (
        a < b if a is not None and isinstance(a, numbers.Number) else False
    ),
    Operator.lte: lambda a, b: (
        a <= b if a is not None and isinstance(a, numbers.Number) else False
    ),
    Operator.gt: lambda a, b: (
        a > b if a is not None and isinstance(a, numbers.Number) else False
    ),
    Operator.gte: lambda a, b: (
        a >= b if a is not None and isinstance(a, numbers.Number) else False
    ),
    Operator.list_contains: lambda a, b: (
        # If user provides a list, check if column value is in it
        a in b
        if isinstance(b, list) and b
        else
        # If column value is a list, check if user value is in it
        b in a if isinstance(a, list) else False
    ),
    Operator.not_in_list: lambda a, b: (
        # If user provides a list, check if column value is NOT in it
        a not in b
        if isinstance(b, list) and b
        else
        # If column value is a list, check if user value is NOT in it
        b not in a if isinstance(a, list) else False
    ),
    Operator.list_intersects: lambda a, b: (
        # Check if there are any common elements between the lists
        bool(set(a) & set(b))
        if isinstance(a, list) and isinstance(b, list)
        else False
    ),
    Operator.list_subset: lambda a, b: (
        # Check if column list is a subset of user's list
        set(a).issubset(set(b))
        if isinstance(a, list) and isinstance(b, list)
        else False
    ),
    Operator.list_superset: lambda a, b: (
        # Check if column list is a superset of user's list
        set(a).issuperset(set(b))
        if isinstance(a, list) and isinstance(b, list)
        else False
    ),
    Operator.list_disjoint: lambda a, b: (
        # Check if lists have no common elements
        set(a).isdisjoint(set(b))
        if isinstance(a, list) and isinstance(b, list)
        else False
    ),
    Operator.starts_with: lambda a, b: (
        a.startswith(b) if isinstance(a, str) and isinstance(b, str) else False
    ),
    Operator.ends_with: lambda a, b: (
        a.endswith(b) if isinstance(a, str) and isinstance(b, str) else False
    ),
    Operator.contains: lambda a, b: (
        b in a if isinstance(a, str) and isinstance(b, str) else False
    ),
}

# Common operators that work with most data types
COMMON_OPERATORS = {
    Operator.eq,
    Operator.neq,
    Operator.exists,
    Operator.not_exists,
}

# Numeric comparison operators
NUMERIC_OPERATORS = {Operator.lt, Operator.lte, Operator.gt, Operator.gte}

# String-specific operators
STRING_OPERATORS = {
    Operator.contains,
    Operator.starts_with,
    Operator.ends_with,
}

# List operations that work with all data types
LIST_OPERATORS = {
    Operator.list_contains,  # Element in list
    Operator.not_in_list,  # Element not in list
    Operator.list_intersects,  # Any common elements
    Operator.list_subset,  # Column list ⊆ user list
    Operator.list_superset,  # Column list ⊇ user list
    Operator.list_disjoint,  # No common elements
}

# Define data type compatibility with operators
data_type_operator_compatibility = {
    "integer": {*COMMON_OPERATORS, *NUMERIC_OPERATORS, *LIST_OPERATORS},
    "float": {*COMMON_OPERATORS, *NUMERIC_OPERATORS, *LIST_OPERATORS},
    "double": {*COMMON_OPERATORS, *NUMERIC_OPERATORS, *LIST_OPERATORS},
    "long": {*COMMON_OPERATORS, *NUMERIC_OPERATORS, *LIST_OPERATORS},
    "boolean": {*COMMON_OPERATORS, *LIST_OPERATORS},
    "string": {*COMMON_OPERATORS, *STRING_OPERATORS, *LIST_OPERATORS},
    "text": {
        *COMMON_OPERATORS,
        *LIST_OPERATORS,
    },  # Form input - no string search operations
    "array": {*COMMON_OPERATORS, *LIST_OPERATORS},
    "object": {*COMMON_OPERATORS, *LIST_OPERATORS},
    "object_id": {*COMMON_OPERATORS, *LIST_OPERATORS},
    "no_op": {*COMMON_OPERATORS, *LIST_OPERATORS},
}
