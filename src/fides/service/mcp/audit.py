"""Audit writer for the mcp_decisions table."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from fides.api.models.mcp_decision import MCPDecision
from fides.service.mcp.models import (
    Decision,
    EvaluationInput,
    IntentResolution,
)


@dataclass
class AuditRecord:
    delivery: str  # "pdp" | "gateway"
    consumer_fides_key: str
    consumer_mode: str | None
    evaluation_input: EvaluationInput
    decision: Decision
    evaluation_ms: int
    tool_name: str | None = None
    tool_schema_hash: str | None = None
    scrubbed_args_hash: str | None = None
    intent_resolution: IntentResolution | None = None
    upstream_id: str | None = None
    intent_ms: int | None = None
    forward_ms: int | None = None
    error_type: str | None = None


class AuditWriter:
    def __init__(self, db: Session) -> None:
        self._db = db

    def record(self, rec: AuditRecord) -> str:
        row_id = uuid.uuid4().hex
        row = MCPDecision(
            id=row_id,
            delivery=rec.delivery,
            consumer_fides_key=rec.consumer_fides_key,
            consumer_mode=rec.consumer_mode,
            upstream_id=rec.upstream_id,
            tool_name=rec.tool_name,
            tool_schema_hash=rec.tool_schema_hash,
            scrubbed_args_hash=rec.scrubbed_args_hash,
            intent_resolution_json=(
                rec.intent_resolution.model_dump(mode="json")
                if rec.intent_resolution else None
            ),
            purpose_source=(
                rec.intent_resolution.purpose_source.value
                if rec.intent_resolution else None
            ),
            chat_context_used=(
                rec.intent_resolution.chat_context_used
                if rec.intent_resolution else False
            ),
            evaluation_input_json=rec.evaluation_input.model_dump(mode="json"),
            decision=rec.decision.decision.value,
            decisive_policy_key=rec.decision.decisive_policy_key,
            action_message=rec.decision.action_message,
            intent_source=(
                rec.intent_resolution.source.value
                if rec.intent_resolution and hasattr(rec.intent_resolution.source, "value")
                else (rec.intent_resolution.source if rec.intent_resolution else None)
            ),
            intent_ms=rec.intent_ms,
            evaluation_ms=rec.evaluation_ms,
            forward_ms=rec.forward_ms,
            error_type=rec.error_type,
        )
        self._db.add(row)
        self._db.commit()
        return row_id
