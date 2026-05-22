"""v2 policy loader.

Phase 1 reality: the v2 PolicyV2 admin surface may not yet be in Fides core.
This loader is the hook — when PolicyV2 lands in the DB, replace the body
of load_enabled_v2_policies with a query.
"""

from __future__ import annotations

from sqlalchemy.orm import Session


def load_enabled_v2_policies(db: Session) -> list[dict]:
    """Return enabled v2 policies as libpbac-shaped dicts.

    Phase 1: returns []. When PolicyV2 lands in Fides, query for enabled
    policies, serialize each to the libpbac dict shape (see the v2 schema
    redesign spec, §2.1) and return the list.
    """
    return []
