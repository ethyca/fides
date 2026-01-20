"""
PolicyV2 Models for runtime policy evaluation.

These models support the Policy Engine v2 which enables runtime evaluation
of privacy policies against system declarations with consent constraint checking.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import (
    BOOLEAN,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base


class PolicyV2Action(StrEnum):
    """Enumeration of policy rule actions."""

    ALLOW = "ALLOW"
    DENY = "DENY"


class PolicyV2MatchType(StrEnum):
    """Enumeration of match types for policy rules."""

    KEY = "key"  # Match against explicit fides_key values
    TAXONOMY = "taxonomy"  # Match against taxonomy tags


class PolicyV2MatchOperator(StrEnum):
    """Enumeration of match operators."""

    ANY = "any"  # Match if ANY value matches (OR logic)
    ALL = "all"  # Match only if ALL values are present (AND logic)


class PolicyV2ConstraintType(StrEnum):
    """Enumeration of constraint types."""

    PRIVACY = "privacy"  # Consent-based constraints
    CONTEXT = "context"  # Environmental constraints (geo, etc.)


class PolicyV2(Base):
    """
    The SQL model for a v2 Policy resource.

    V2 Policies are organizational rules that define what data uses are permitted
    or denied, evaluated at runtime via the /evaluate endpoint.
    """

    __tablename__ = "policy_v2"

    fides_key = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(BOOLEAN, server_default="t", nullable=False)

    # Relationship to rules
    rules = relationship(
        "PolicyV2Rule",
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PolicyV2Rule.order",
    )

    @classmethod
    def create(
        cls: Type["PolicyV2"],
        db: Session,
        *,
        data: Dict[str, Any],
    ) -> "PolicyV2":
        """Create a new PolicyV2 with its rules."""
        rules_data = data.pop("rules", [])

        # Create the policy
        policy = cls(**data)
        db.add(policy)
        db.flush()

        # Create rules
        for idx, rule_data in enumerate(rules_data):
            rule_data["policy_id"] = policy.id
            rule_data["order"] = rule_data.get("order", idx)
            PolicyV2Rule.create(db, data=rule_data)

        db.commit()
        db.refresh(policy)
        return policy

    def update(
        self,
        db: Session,
        *,
        data: Dict[str, Any],
    ) -> "PolicyV2":
        """Update a PolicyV2 and its rules."""
        rules_data = data.pop("rules", None)

        # Update policy fields
        for key, value in data.items():
            setattr(self, key, value)

        # If rules provided, replace all rules
        if rules_data is not None:
            # Delete existing rules (cascade will handle matches and constraints)
            for rule in self.rules:
                db.delete(rule)
            db.flush()

            # Create new rules
            for idx, rule_data in enumerate(rules_data):
                rule_data["policy_id"] = self.id
                rule_data["order"] = rule_data.get("order", idx)
                PolicyV2Rule.create(db, data=rule_data)

        db.commit()
        db.refresh(self)
        return self

    @classmethod
    def get_by_fides_key(cls, db: Session, fides_key: str) -> Optional["PolicyV2"]:
        """Get a policy by its fides_key."""
        return db.query(cls).filter(cls.fides_key == fides_key).first()

    @classmethod
    def get_all_enabled(cls, db: Session) -> List["PolicyV2"]:
        """Get all enabled policies."""
        return db.query(cls).filter(cls.enabled == True).all()  # noqa: E712

    def delete(self, db: Session) -> None:
        """Delete this policy and all associated rules."""
        db.delete(self)
        db.commit()


class PolicyV2Rule(Base):
    """
    The SQL model for a v2 Policy Rule.

    Rules define match conditions and actions (ALLOW/DENY) within a policy.
    """

    __tablename__ = "policy_v2_rule"

    policy_id = Column(
        String(255),
        ForeignKey("policy_v2.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    action = Column(String, nullable=False)  # ALLOW or DENY
    order = Column(Integer, server_default="0", nullable=False)
    on_denial_message = Column(Text, nullable=True)

    # Relationships
    policy = relationship("PolicyV2", back_populates="rules")
    matches = relationship(
        "PolicyV2RuleMatch",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    constraints = relationship(
        "PolicyV2RuleConstraint",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @classmethod
    def create(
        cls: Type["PolicyV2Rule"],
        db: Session,
        *,
        data: Dict[str, Any],
    ) -> "PolicyV2Rule":
        """Create a new rule with its matches and constraints."""
        matches_data = data.pop("matches", [])
        constraints_data = data.pop("constraints", [])

        # Create the rule
        rule = cls(**data)
        db.add(rule)
        db.flush()

        # Create matches
        for match_data in matches_data:
            match_data["rule_id"] = rule.id
            match = PolicyV2RuleMatch(**match_data)
            db.add(match)

        # Create constraints
        for constraint_data in constraints_data:
            constraint_data["rule_id"] = rule.id
            constraint = PolicyV2RuleConstraint(**constraint_data)
            db.add(constraint)

        db.flush()
        return rule


class PolicyV2RuleMatch(Base):
    """
    The SQL model for a v2 Policy Rule Match condition.

    Matches define how rules match against privacy declarations.
    Supports both key-based matching (data_category, data_use, data_subject)
    and taxonomy-based matching (via TaxonomyUsage).
    """

    __tablename__ = "policy_v2_rule_match"

    rule_id = Column(
        String(255),
        ForeignKey("policy_v2_rule.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_type = Column(String, nullable=False)  # 'key' or 'taxonomy'
    target_field = Column(
        String, nullable=False
    )  # data_category, data_use, data_subject, data_use_taxonomies, data_category_taxonomies
    operator = Column(String, server_default="any", nullable=False)  # 'any' or 'all'
    values = Column(JSONB, nullable=False)  # List of keys or {taxonomy, element} objects

    # Relationship
    rule = relationship("PolicyV2Rule", back_populates="matches")


class PolicyV2RuleConstraint(Base):
    """
    The SQL model for a v2 Policy Rule Constraint.

    Constraints define additional conditions that must be met for ALLOW rules.
    Supports privacy constraints (consent checks) and context constraints (geo, etc.).
    """

    __tablename__ = "policy_v2_rule_constraint"

    rule_id = Column(
        String(255),
        ForeignKey("policy_v2_rule.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    constraint_type = Column(String, nullable=False)  # 'privacy' or 'context'
    configuration = Column(JSONB, nullable=False)  # Constraint-specific config

    # Relationship
    rule = relationship("PolicyV2Rule", back_populates="constraints")
