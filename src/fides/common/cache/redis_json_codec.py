"""JSON encode/decode for Redis-cached objects (matches FidesopsRedis semantics).

Kept in ``fides.common.cache`` so DSRCacheStore can serialize consistently with
``FidesopsRedis.set_encoded_object`` / ``get_encoded_by_key`` without importing
``fides.api.util.cache`` (circular import).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import unquote_to_bytes

from loguru import logger

from fides.api.util.custom_json_encoder import CustomJSONEncoder, _custom_decoder


def encode_cache_obj(obj: Any) -> str:
    """Encode a Python object to the same JSON string used by ``FidesopsRedis.encode_obj``."""
    return json.dumps(obj, cls=CustomJSONEncoder)  # type: ignore[arg-type]


def decode_cache_obj(bs: Optional[str]) -> Optional[Any]:
    """Decode JSON cached by ``encode_cache_obj`` (same rules as ``FidesopsRedis.decode_obj``)."""
    if not bs:
        return None
    try:
        result = json.loads(bs, object_hook=_custom_decoder)
    except json.JSONDecodeError:
        logger.info(
            "Error decoding cache. If you are coming from a version of fides prior to 2.8 "
            "this could be an issue with cache format and the request needs to be reprocessed."
        )
        return None
    if isinstance(result, str) and result.startswith("quote_encoded"):
        result = unquote_to_bytes(result)[14:]
    return result
