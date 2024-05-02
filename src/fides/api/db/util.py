# pylint: skip-file
from json import dumps, loads
from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from fides.api.util.custom_json_encoder import CustomJSONEncoder, _custom_decoder

if TYPE_CHECKING:
    # Override the Enum constructor not to accept a list of strings and confuse mypy:
    # https://github.com/dropbox/sqlalchemy-stubs/issues/114#issuecomment-541770319
    from sqlalchemy.sql.type_api import TypeEngine

    T = TypeVar("T")

    class EnumColumn(TypeEngine[T]):
        def __init__(self, enum: Type[T], **kwargs: Any) -> None: ...

else:
    from sqlalchemy import Enum as EnumColumn


def custom_json_deserializer(string: str) -> Dict:
    """
    JSON deserializer function to be used in SQLAlchemy engine creation.
    Leverages our custom JSON decoder function, which deserializes JSON
    data that's been serialized with the CustomJSONEncoder,
    to handle data types not supported by json.dumps() and json.loads()
    """
    return loads(string, object_hook=_custom_decoder)


def custom_json_serializer(obj: Any) -> str:
    """
    JSON serializer function to be used in SQLAlchemy engine creation.
    Leverages our CustomJSONEncoder, which can serialize data types that are
    not supported by json.dumps()
    """
    return dumps(obj, cls=CustomJSONEncoder)
