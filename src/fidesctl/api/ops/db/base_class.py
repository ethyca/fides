from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy_utils import JSONType


class JSONTypeOverride(JSONType):  # pylint: disable=W0223
    """
    Temporary override of JSONType with workaround to fix the return type.

    Using a StringEncryptedType with JSONType as the underlying type returns a string instead of a dictionary:
    '{"key": "value"}' instead of {"key": "value"}

    https://github.com/kvesteri/sqlalchemy-utils/issues/532
    """

    def process_bind_param(self, value: MutableDict, _: Any | None) -> str | None:
        """
        Overrides JSONType.process_bind_param to return json.dumps(value) instead of just the value.
        """
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value: str, _: Any | None) -> dict[str, Any] | None:
        """
        Overrides JSONType.process_result_value to return json.loads(value) instead of just the value.
        """
        if value is not None:
            return json.loads(value)
        return value
