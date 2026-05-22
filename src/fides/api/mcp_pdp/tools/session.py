"""set_session_purpose MCP tool."""

from sqlalchemy.orm import Session

from fides.api.mcp_pdp.session_store import SessionStore
from fides.api.models.mcp_consumer_settings import MCPConsumerSettings

_SESSIONS = SessionStore()


def _get_db_session() -> Session:
    """Return a new DB session. Isolated function so tests can patch it."""
    from fides.common.session_management import get_api_session
    return get_api_session()


async def set_session_purpose(
    *,
    session_id: str,
    consumer_fides_key: str,
    purpose: str,
) -> dict:
    """Set the session-scoped purpose for an interactive-mode consumer."""
    with _get_db_session() as db:
        row = (
            db.query(MCPConsumerSettings)
            .filter(MCPConsumerSettings.consumer_fides_key == consumer_fides_key)
            .one_or_none()
        )
        if row is None:
            raise ValueError(f"unknown consumer {consumer_fides_key!r}")
        if purpose not in (row.allowable_purpose_keys or []):
            raise ValueError(
                f"purpose {purpose!r} not in allowable_purpose_keys for {consumer_fides_key!r}"
            )
    _SESSIONS.set(session_id, purpose)
    return {"session_id": session_id, "purpose": purpose}
