import json
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict
from urllib.parse import quote, unquote_to_bytes

from bson.objectid import ObjectId

ENCODED_BYTES_PREFIX = "quote_encoded_"
ENCODED_DATE_PREFIX = "date_encoded_"
ENCODED_MONGO_OBJECT_ID_PREFIX = "encoded_object_id_"


class CustomJSONEncoder(json.JSONEncoder):
    """
    CustomJSONEncoder that extends the builtin JSONEncoder,
    used to handle serialization of data types not supported by
    json.dumps().

    This encoder can be used for JSON serialization for storage in
    the redis cache, as well as our DB JSONB columns/fields.
    """

    def default(self, o: Any) -> Any:  # pylint: disable=too-many-return-statements
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, bytes):
            return f"{ENCODED_BYTES_PREFIX}{quote(o)}"
        if isinstance(o, (datetime, date)):
            return f"{ENCODED_DATE_PREFIX}{o.isoformat()}"
        if isinstance(o, ObjectId):
            return f"{ENCODED_MONGO_OBJECT_ID_PREFIX}{str(o)}"
        if isinstance(o, object):
            if hasattr(o, "__dict__"):
                return o.__dict__
            if not isinstance(o, int) and not isinstance(o, float):
                return str(o)

        # It doesn't seem possible to make it here, but I'm leaving in as a fail safe
        # just in case.
        return super().default(o)  # pragma: no cover


def _custom_decoder(json_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom JSON decoder that deserializes data that's been serialized,
    by the CustomJSONEncoder, which is used used to handle serialization
    of data types not supported by json.dumps().

    This encoder can be used for JSON deserialization for storage in
    the redis cache, as well as our DB JSONB columns/fields.
    """
    for k, v in json_dict.items():
        if isinstance(v, str):
            # The mongodb objectids couldn't be directly json encoded so they are converted
            # to strings and prefixed with encoded_object_id in order to find during decodeint.
            if v.startswith(ENCODED_MONGO_OBJECT_ID_PREFIX):
                json_dict[k] = ObjectId(v[18:])
            if v.startswith(ENCODED_DATE_PREFIX):
                json_dict[k] = datetime.fromisoformat(v[13:])
            # The bytes from secrets couldn't be directly json encoded so it is url
            # encode and prefixed with quite_encoded in order to find during decodeint.
            elif v.startswith(ENCODED_BYTES_PREFIX):
                json_dict[k] = unquote_to_bytes(v)[14:]

    return json_dict
