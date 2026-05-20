"""Pydantic models for the MCP policy core.

Public types only. No I/O, no DB, no LLM client. Consumed by every other
file in fides/service/mcp/ and by fides/api/mcp_pdp/.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class ConsumerMode(str, Enum):
    AGENT = "agent"
    INTERACTIVE = "interactive"


class PurposeSource(str, Enum):
    DECLARED = "declared"
    EXPLICIT_HINT = "explicit_hint"
    SESSION = "session"
    INFERRED = "inferred"


class DecisionOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    NO_DECISION = "NO_DECISION"


class IntentSource(str, Enum):
    CACHE = "cache"
    INFERENCE = "inference"
    FALLBACK = "fallback"


class Consumer(BaseModel):
    model_config = ConfigDict(frozen=True)

    fides_key: str
    mode: ConsumerMode
    allowable_purpose_keys: list[str]
    chat_context_inference: bool = False
    confidence_floor_overrides: dict[str, float] | None = None


class ChatContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    recent_user_messages: list[str] = Field(default_factory=list)
    conversation_summary: str | None = None
    active_user_intent: str | None = None


class RegisteredTool(BaseModel):
    upstream_key: str
    tool_name: str
    description: str
    input_schema: dict[str, Any]

    @computed_field  # type: ignore[misc]
    @property
    def tool_schema_hash(self) -> str:
        canonical = json.dumps(self.input_schema, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ScrubResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    scrubbed_text: str
    scrubbed_hash: str


class CapabilityProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    upstream_key: str
    tool_name: str
    tool_schema_hash: str
    plausible_data_categories: list[str]
    base_confidence: float = Field(ge=0.0, le=1.0)
    model_used: str


class IntentResolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Resolved policy inputs
    data_use: str
    data_categories: list[str]
    data_subject: str | None

    # Provenance
    purpose_source: PurposeSource
    chat_context_used: bool

    # Inference metadata
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    source: IntentSource | Literal["cache", "inference", "fallback"]
    model: str | None
    tool_capability_profile_hash: str
    scrubbed_args_hash: str

    @field_validator("source", mode="before")
    @classmethod
    def _coerce_source(cls, v: Any) -> Any:
        return IntentSource(v) if isinstance(v, str) else v


class EvaluationInput(BaseModel):
    """The MCP-native shape passed to fides/service/mcp/evaluator.py."""

    model_config = ConfigDict(frozen=True)

    consumer_fides_key: str
    data_use: str
    data_categories: list[str]
    data_subject: str | None = None
    environment: dict[str, Any] = Field(default_factory=dict)


class EvaluatedPolicy(BaseModel):
    policy_key: str
    priority: int
    matched: bool
    result: Literal["ALLOW", "DENY", "SUPPRESSED"]
    unless_triggered: bool


class Decision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: DecisionOutcome
    decisive_policy_key: str | None = None
    action_message: str | None = None
    evaluated_policies: list[EvaluatedPolicy] = Field(default_factory=list)
