"""In-memory session-id → session_purpose store.

Lifetime: process. Phase 1 doesn't share session purpose across replicas;
multi-replica session purpose is a Phase 2 / Companion concern.
"""

from __future__ import annotations

from threading import RLock


class SessionStore:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._lock = RLock()

    def set(self, session_id: str, purpose: str) -> None:
        with self._lock:
            self._data[session_id] = purpose

    def get(self, session_id: str) -> str | None:
        with self._lock:
            return self._data.get(session_id)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._data.pop(session_id, None)
