"""Tests for the MCP policy loader."""

from __future__ import annotations

from sqlalchemy.orm import Session

from fides.api.models.access_policy import AccessPolicy, AccessPolicyVersion


def test_load_returns_empty_when_no_policies_seeded(db: Session):
    from fides.service.mcp.policy_loader import load_enabled_v2_policies

    result = load_enabled_v2_policies(db)
    assert result == []


def _seed_policy(
    db: Session,
    *,
    name: str,
    yaml_body: str,
    enabled: bool = True,
    is_deleted: bool = False,
    version: int = 1,
) -> AccessPolicy:
    policy = AccessPolicy(name=name, enabled=enabled, is_deleted=is_deleted)
    db.add(policy)
    db.flush()
    db.add(AccessPolicyVersion(access_policy_id=policy.id, version=version, yaml=yaml_body))
    db.flush()
    return policy


_BASIC_ALLOW_YAML = """
decision: ALLOW
priority: 100
match:
  data_use:
    any:
      - essential.service.operations.support
"""


def test_load_excludes_disabled_policies(db: Session):
    from fides.service.mcp.policy_loader import (
        invalidate_cache,
        load_enabled_v2_policies,
    )

    _seed_policy(db, name="enabled-one", yaml_body=_BASIC_ALLOW_YAML, enabled=True)
    _seed_policy(db, name="disabled-one", yaml_body=_BASIC_ALLOW_YAML, enabled=False)
    invalidate_cache()

    result = load_enabled_v2_policies(db)
    assert len(result) == 1


def test_load_excludes_soft_deleted_policies(db: Session):
    from fides.service.mcp.policy_loader import (
        invalidate_cache,
        load_enabled_v2_policies,
    )

    _seed_policy(db, name="alive", yaml_body=_BASIC_ALLOW_YAML, enabled=True, is_deleted=False)
    _seed_policy(db, name="dead", yaml_body=_BASIC_ALLOW_YAML, enabled=True, is_deleted=True)
    invalidate_cache()

    result = load_enabled_v2_policies(db)
    assert len(result) == 1


def test_load_picks_latest_version_per_policy(db: Session):
    from fides.service.mcp.policy_loader import (
        invalidate_cache,
        load_enabled_v2_policies,
    )

    older = """
decision: ALLOW
priority: 1
"""
    newer = """
decision: DENY
priority: 9
"""
    policy = AccessPolicy(name="versioned", enabled=True, is_deleted=False)
    db.add(policy)
    db.flush()
    db.add(AccessPolicyVersion(access_policy_id=policy.id, version=1, yaml=older))
    db.add(AccessPolicyVersion(access_policy_id=policy.id, version=2, yaml=newer))
    db.flush()
    invalidate_cache()

    result = load_enabled_v2_policies(db)
    assert len(result) == 1
    assert result[0]["decision"] == "DENY"
    assert result[0]["priority"] == 9


def test_load_normalizes_default_priority_unless_action(db: Session):
    from fides.service.mcp.policy_loader import (
        invalidate_cache,
        load_enabled_v2_policies,
    )

    minimal_yaml = "decision: ALLOW\n"
    _seed_policy(db, name="minimal", yaml_body=minimal_yaml)
    invalidate_cache()

    result = load_enabled_v2_policies(db)
    assert len(result) == 1
    p = result[0]
    assert p["priority"] == 0
    assert p["match"] == {}
    assert p["unless"] == []
    assert p["action"] == {}
    assert p["enabled"] is True
