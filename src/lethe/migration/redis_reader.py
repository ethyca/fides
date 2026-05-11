"""Read legacy DSR-related keys from Redis (pre–Postgres DSRStore migration)."""

from __future__ import annotations

import json
import re
from typing import Any, Iterator, Optional, Set

# Typical privacy_request.id is a UUID string; keys look like ``id-{uuid}-...``.
_PR_ID_IN_KEY = re.compile(
    r"^id-([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})-"
)
_DSR_PREFIX = re.compile(r"^dsr:([^:]+):")


def extract_privacy_request_id_from_key(key: str) -> Optional[str]:
    """Return the privacy request id embedded in a legacy Redis key, if any."""
    m = _PR_ID_IN_KEY.match(key)
    if m:
        return m.group(1)
    m2 = _DSR_PREFIX.match(key)
    if m2:
        return m2.group(1)
    return None


def iter_scan_keys(redis: Any, pattern: str) -> Iterator[str]:
    """Yield keys matching ``pattern`` using non-blocking SCAN."""
    cursor: Any = 0
    while True:
        cursor, keys = redis.scan(cursor=cursor, match=pattern, count=500)
        for k in keys:
            if isinstance(k, bytes):
                yield k.decode("utf-8", errors="replace")
            else:
                yield str(k)
        if cursor in (0, "0"):
            break


def discover_privacy_request_ids(redis: Any) -> Set[str]:
    """Collect privacy request ids referenced by legacy DSR Redis keys."""
    ids: Set[str] = set()
    patterns = (
        "dsr:*",
        "id-*-identity-*",
        "id-*-drp-*",
        "id-*-encryption-*",
        "id-*-async-execution",
        "id-*-privacy-request-retry-count*",
    )
    for pat in patterns:
        for key in iter_scan_keys(redis, pat):
            pr_id = extract_privacy_request_id_from_key(key)
            if pr_id:
                ids.add(pr_id)
    return ids


def _maybe_decode_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def read_string(redis: Any, key: str) -> Optional[str]:
    raw = redis.get(key)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def load_drp_attrs_from_redis(redis: Any, privacy_request_id: str) -> dict[str, Any]:
    """Merge DRP attributes from ``dsr:{id}:drp:*`` and ``id-{id}-drp-*`` keys."""
    drp: dict[str, Any] = {}
    for key in iter_scan_keys(redis, f"dsr:{privacy_request_id}:drp:*"):
        parts = key.split(":", 3)
        if len(parts) >= 4 and parts[2] == "drp":
            attr = parts[3]
            val = read_string(redis, key)
            if val is not None:
                drp[attr] = _maybe_decode_json(val)
    prefix = f"id-{privacy_request_id}-drp-"
    for key in iter_scan_keys(redis, f"id-{privacy_request_id}-drp-*"):
        if not key.startswith(prefix):
            continue
        attr = key[len(prefix) :]
        val = read_string(redis, key)
        if val is not None:
            drp.setdefault(attr, _maybe_decode_json(val))
    return drp
