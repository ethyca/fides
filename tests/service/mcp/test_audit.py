import pytest
from sqlalchemy.orm import Session

from fides.api.models.mcp_decision import MCPDecision
from fides.service.mcp.audit import AuditRecord, AuditWriter
from fides.service.mcp.models import (
    Decision,
    DecisionOutcome,
    EvaluationInput,
    IntentResolution,
    IntentSource,
    PurposeSource,
)


def _resolution() -> IntentResolution:
    return IntentResolution(
        data_use="essential.service.operations.support",
        data_categories=["user.contact.email"],
        data_subject="customer",
        purpose_source=PurposeSource.DECLARED,
        chat_context_used=False,
        confidence=0.95,
        rationale="",
        source=IntentSource.INFERENCE,
        model="claude-haiku-4-5",
        tool_capability_profile_hash="abc",
        scrubbed_args_hash="def",
    )


def _decision() -> Decision:
    return Decision(decision=DecisionOutcome.ALLOW, decisive_policy_key="x", action_message=None)


def _eval_input() -> EvaluationInput:
    return EvaluationInput(
        consumer_fides_key="acme",
        data_use="essential.service.operations.support",
        data_categories=["user.contact.email"],
        data_subject="customer",
    )


def test_audit_record_persists_all_fields(db: Session):
    writer = AuditWriter(db)
    writer.record(AuditRecord(
        delivery="pdp",
        consumer_fides_key="acme",
        consumer_mode="agent",
        tool_name="get_ticket",
        tool_schema_hash="abc",
        scrubbed_args_hash="def",
        intent_resolution=_resolution(),
        evaluation_input=_eval_input(),
        decision=_decision(),
        intent_ms=210,
        evaluation_ms=4,
    ))
    row = db.query(MCPDecision).first()
    assert row is not None
    assert row.delivery == "pdp"
    assert row.consumer_fides_key == "acme"
    assert row.decision == "ALLOW"
    assert row.purpose_source == "declared"
    assert row.chat_context_used is False
    assert row.evaluation_ms == 4


def test_audit_record_evaluate_policy_callsite_no_intent(db: Session):
    """evaluate_policy callers don't have an IntentResolution — should still persist."""
    writer = AuditWriter(db)
    writer.record(AuditRecord(
        delivery="pdp",
        consumer_fides_key="acme",
        consumer_mode=None,
        tool_name=None,
        intent_resolution=None,
        evaluation_input=_eval_input(),
        decision=_decision(),
        intent_ms=None,
        evaluation_ms=3,
    ))
    row = db.query(MCPDecision).first()
    assert row.intent_resolution_json is None
    assert row.purpose_source is None
