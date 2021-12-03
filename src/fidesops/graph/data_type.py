import logging
from abc import abstractmethod, ABC
from typing import Generic, Optional, Any, TypeVar
from enum import Enum

from bson.errors import InvalidId
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)
T = TypeVar("T")


class DataTypeConverter(ABC, Generic[T]):
    """DataTypeConverters are responsible for converting types of other values into the type represented here."""

    @abstractmethod
    def to_value(self, other: Any) -> Optional[T]:
        """How to convert from another datatype value to this type. When extending DataTypeConverter this method should
            return either a T or None in every case and never raise an Exception.
        an Exception."""

    @abstractmethod
    def empty_value(self) -> T:
        """A value that represents `empty` in whatever way makes sense for type T"""

    def truncate(self, length: int, val: T) -> T:
        """Truncates value to given length"""
        logger.warning(
            f"{self.__class__.__name__} does not support length truncation. Using original masked value instead for update query."
        )
        return val


class StringTypeConverter(DataTypeConverter[str]):
    """String data type converter. This type just uses str() type conversion."""

    def to_value(self, other: Any) -> Optional[str]:
        """Convert to str"""
        return str(other) if other else None

    def empty_value(self) -> str:
        """Empty string value"""
        return ""

    def truncate(self, length: int, val: str) -> str:
        """Truncates value to given length"""
        return val[:length]


class IntTypeConverter(DataTypeConverter[int]):
    """Int data type converter. This type just uses built-in int() type conversion."""

    def to_value(self, other: Any) -> Optional[int]:
        """Convert to int"""
        try:
            return int(other)

        except (ValueError, TypeError):
            return None

    def empty_value(self) -> int:
        """Empty int value"""
        return 0


class FloatTypeConverter(DataTypeConverter[float]):
    """Float data type converter. This type just uses built-in float() type conversion."""

    def to_value(self, other: Any) -> Optional[float]:
        """Convert to float"""
        try:
            return float(other)

        except (ValueError, TypeError):
            return None

    def empty_value(self) -> float:
        """Empty float value"""
        return 0.0


class BooleanTypeConverter(DataTypeConverter[bool]):
    """Boolean data type converter recognizing the strings True/False, 1,0, and booleans."""

    true_vals = {"True", "true", True, 1}
    false_vals = {"False", "false", False, 0}

    def to_value(self, other: Any) -> Optional[bool]:
        """Convert to bool"""
        if other in BooleanTypeConverter.true_vals:
            return True
        if other in BooleanTypeConverter.false_vals:
            return False
        return None

    def empty_value(self) -> bool:
        """Empty boolean value"""
        return False


class ObjectIdTypeConverter(DataTypeConverter[ObjectId]):
    """ObjectId data type converter, allowing for conversions from strings only."""

    def to_value(self, other: Any) -> Optional[ObjectId]:
        """Convert to ObjectId."""
        t = type(other)
        if t == ObjectId:
            return other
        if t == str and len(other) == 24:
            try:
                return ObjectId(other)
            except (InvalidId, TypeError) as e:
                print(e)
                return None
        return None

    def empty_value(self) -> ObjectId:
        """Empty objectId value"""
        return ObjectId("000000000000000000000000")


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
