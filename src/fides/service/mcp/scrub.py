"""PII scrubbing for MCP inference inputs.

The scrubber is a stateless transform: arbitrary text or dicts in, a
ScrubResult with type-token-replaced text and a stable hash out. The
original input is never persisted. The hash is used as a cache key,
so structurally identical calls (different PII values) share a key.

Replace the regex implementation with an ML-based one later (see
spec §11) by providing a different Scrubber instance.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Protocol, runtime_checkable

from fides.service.mcp.models import ScrubResult


@runtime_checkable
class Scrubber(Protocol):
    def scrub(self, text: str) -> ScrubResult: ...
    def scrub_dict(self, value: dict[str, Any]) -> ScrubResult: ...


_EMAIL_RE = re.compile(r"\b[\w.+\-]+@[\w\-]+\.[\w.\-]+\b")
_PHONE_RE = re.compile(r"\+?\d[\d\-\s.()]{7,}\d")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_TOKEN_RE = re.compile(r"\b[A-Fa-f0-9]{32,}\b|\b[A-Za-z0-9+/=_-]{32,}\b")
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def _luhn_ok(digits: str) -> bool:
    s = [int(c) for c in digits if c.isdigit()]
    if len(s) < 13 or len(s) > 19:
        return False
    total = 0
    for i, d in enumerate(reversed(s)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _scrub_card(match: re.Match[str]) -> str:
    raw = match.group(0)
    return "<payment_card>" if _luhn_ok(raw) else raw


def _scrub_text(text: str) -> str:
    out = text
    out = _EMAIL_RE.sub("<email>", out)
    out = _SSN_RE.sub("<gov_id>", out)
    out = _CARD_RE.sub(_scrub_card, out)
    out = _IPV4_RE.sub("<ip_address>", out)
    out = _PHONE_RE.sub(
        lambda m: "<phone>" if sum(c.isdigit() for c in m.group(0)) >= 8 else m.group(0),
        out,
    )
    out = _TOKEN_RE.sub("<token>", out)
    return out


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class RegexScrubber:
    """Default v1 scrubber. Regex-based, fast, deterministic, partial recall.

    See spec §5.4 for tradeoffs and the path to ML-based scrubbing.
    """

    def scrub(self, text: str) -> ScrubResult:
        scrubbed = _scrub_text(text)
        return ScrubResult(scrubbed_text=scrubbed, scrubbed_hash=_hash(scrubbed))

    def scrub_dict(self, value: dict[str, Any]) -> ScrubResult:
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
        scrubbed = _scrub_text(canonical)
        return ScrubResult(scrubbed_text=scrubbed, scrubbed_hash=_hash(scrubbed))
