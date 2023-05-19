from typing import TypeVar, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.sql.type_api import TypeEngine

    T = TypeVar("T")

    class EnumColumn(TypeEngine[T]):
        def __init__(self, enum: Type[T]) -> None:
            ...

else:
    from sqlalchemy import Enum as EnumColumn
