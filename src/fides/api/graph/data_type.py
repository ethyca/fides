from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, Optional, Set, Tuple, TypeVar

from bson.errors import InvalidId
from bson.objectid import ObjectId
from loguru import logger

T = TypeVar("T")


class DataTypeConverter(ABC, Generic[T]):
    """DataTypeConverters are responsible for converting types of other values into the type represented here."""

    def __init__(self, name: str, empty_val: T):
        self.name = name
        self.empty_val = empty_val

    @abstractmethod
    def to_value(self, other: Any) -> Optional[T]:
        """How to convert from another datatype value to this type. When extending DataTypeConverter this method should
            return either a T or None in every case and never raise an Exception.
        an Exception."""

    def empty_value(self) -> T:
        """A value that represents `empty` in whatever way makes sense for type T"""
        return self.empty_val

    def truncate(self, length: int, val: T) -> T:
        """Truncates value to given length"""
        logger.warning(
            "{} does not support length truncation. Using original masked value instead for update query.",
            self.name,
        )
        return val

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataTypeConverter):
            return False

        return self.__dict__ == other.__dict__


class NoOpTypeConverter(DataTypeConverter[Any]):
    """Placeholder No-op converter. This type is assigned to fields when type is unspecified."""

    def __init__(self) -> None:
        super().__init__(name="None", empty_val=None)

    def to_value(self, other: Any) -> Optional[Any]:
        """no-op"""
        return other

    def truncate(self, length: int, val: Any) -> Any:
        """No action"""
        return val


class StringTypeConverter(DataTypeConverter[str]):
    """String data type converter. This type just uses str() type conversion."""

    def __init__(self) -> None:
        super().__init__(name="string", empty_val="")

    def to_value(self, other: Any) -> Optional[str]:
        """Convert to str"""
        return str(other) if other else None

    def truncate(self, length: int, val: str) -> str:
        """Truncates value to given length"""
        return val[:length]


class IntTypeConverter(DataTypeConverter[int]):
    """Int data type converter. This type just uses built-in int() type conversion."""

    def __init__(self) -> None:
        super().__init__(name="integer", empty_val=0)

    def to_value(self, other: Any) -> Optional[int]:
        """Convert to int"""
        try:
            return int(other)

        except (ValueError, TypeError):
            return None


class FloatTypeConverter(DataTypeConverter[float]):
    """Float data type converter. This type just uses built-in float() type conversion."""

    def __init__(self) -> None:
        super().__init__(name="float", empty_val=0.0)

    def to_value(self, other: Any) -> Optional[float]:
        """Convert to float"""
        try:
            return float(other)

        except (ValueError, TypeError):
            return None


class BooleanTypeConverter(DataTypeConverter[bool]):
    """Boolean data type converter recognizing the strings True/False, 1,0, and booleans."""

    def __init__(self) -> None:
        super().__init__(name="boolean", empty_val=False)

    true_vals = ("True", "true", True, 1)
    false_vals = ("False", "false", False, 0)

    def to_value(self, other: Any) -> Optional[bool]:
        """Convert to bool"""
        if other in BooleanTypeConverter.true_vals:
            return True
        if other in BooleanTypeConverter.false_vals:
            return False
        return None


class ObjectIdTypeConverter(DataTypeConverter[ObjectId]):
    """ObjectId data type converter, allowing for conversions from strings only."""

    def __init__(self) -> None:
        super().__init__(
            name="object_id", empty_val=ObjectId("000000000000000000000000")
        )

    def to_value(self, other: Any) -> Optional[ObjectId]:
        """Convert to ObjectId."""
        t = type(other)
        if t == ObjectId:
            return other
        if t == str and len(other) == 24:
            try:
                return ObjectId(other)
            except (InvalidId, TypeError):
                return None
        return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ObjectTypeConverter):
            return False

        return self.__dict__ == other.__dict__


class ObjectTypeConverter(DataTypeConverter[Dict[str, Any]]):
    """Json data type converter."""

    def __init__(self) -> None:
        super().__init__(name="object", empty_val={})

    def to_value(self, other: Any) -> Optional[Dict[str, Any]]:
        """Pass through dict values."""
        if isinstance(other, dict):
            return other
        return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ObjectTypeConverter):
            return False

        return self.__dict__ == other.__dict__


class DataType(Enum):
    """Supported data types for data retrieval and erasure.

    This type list is based on json-schema, with some alterations:
    - mongo_object_id is added to address mongodb keys
    - the json-schema 'null' type is omitted
    """

    string = StringTypeConverter()
    integer = IntTypeConverter()
    float = FloatTypeConverter()
    boolean = BooleanTypeConverter()
    object_id = ObjectIdTypeConverter()
    object = ObjectTypeConverter()
    no_op = NoOpTypeConverter()


_data_type_names: Set[str] = {
    "string",
    "integer",
    "float",
    "boolean",
    "object_id",
    "object",
}


def is_valid_data_type(type_name: str) -> bool:
    """Is this type a valid data type identifier"""
    return type_name is None or type_name in _data_type_names


def get_data_type_converter(type_name: Optional[str]) -> DataTypeConverter:
    """Return the matching type converter. If an empty string or None or string None is passed in
    will return the No-op converter, so the converter will never be set to 'None'.

    Only an illegal key will raise a KeyError."""
    if not type_name or type_name == "None":
        return DataType.no_op.value
    return DataType[type_name].value


def parse_data_type_string(type_string: Optional[str]) -> Tuple[Optional[str], bool]:
    """Parse the data type string. Arrays are expressed in the form 'type[]'.

    e.g.
    - 'string' -> ('string', false)
    - 'string[]' -> ('string', true)
    """
    if not type_string:
        return None, False
    idx = type_string.find("[]")
    if idx == -1:
        return type_string, False
    return type_string[:idx], True


def to_data_type_string(data_type: str, is_array: bool) -> str:
    """
    Appends [] to the data type if it is an array.
    """
    if data_type == DataType.no_op.name:
        return data_type
    return data_type + "[]" if is_array else data_type


def get_data_type(value: Any) -> Tuple[Optional[str], bool]:
    """
    Returns the simple or array type of the given value.
    """

    data_type = DataType.no_op.name
    is_array = False

    # cannot assume data type for missing or empty values
    if value in (None, "", [], {}):
        return data_type, is_array

    if isinstance(value, bool):
        data_type = DataType.boolean.name
    elif isinstance(value, int):
        data_type = DataType.integer.name
    elif isinstance(value, float):
        data_type = DataType.float.name
    elif isinstance(value, str):
        data_type = DataType.string.name
    elif isinstance(value, dict):
        data_type = DataType.object.name
    elif isinstance(value, list):
        is_array = True
        if all(isinstance(item, int) for item in value):
            data_type = DataType.integer.name
        elif all(isinstance(item, float) for item in value):
            data_type = DataType.float.name
        elif all(isinstance(item, str) for item in value):
            data_type = DataType.string.name
        elif all(isinstance(item, dict) for item in value):
            data_type = DataType.object.name
    return data_type, is_array


if __name__ == "__main__":  # pragma: no cover
    v = DataType.no_op.value
    for x in v.__dict__:
        print(x)
    print(v)
