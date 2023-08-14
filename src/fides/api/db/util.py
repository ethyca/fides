# pylint: skip-file
from typing import TYPE_CHECKING, Any, Type, TypeVar

if TYPE_CHECKING:
    # Override the Enum constructor not to accept a list of strings and confuse mypy:
    # https://github.com/dropbox/sqlalchemy-stubs/issues/114#issuecomment-541770319
    from sqlalchemy.sql.type_api import TypeEngine

    T = TypeVar("T")

    class EnumColumn(TypeEngine[T]):
        def __init__(self, enum: Type[T], **kwargs: Any) -> None:
            ...

else:
    from sqlalchemy import Enum as EnumColumn
