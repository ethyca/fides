from fides.service.mcp.models import (
    CapabilityProfile,
    ChatContext,
    Consumer,
    ConsumerMode,
    Decision,
    DecisionOutcome,
    EvaluationInput,
    IntentResolution,
    PurposeSource,
    RegisteredTool,
    ScrubResult,
)


def test_intent_resolution_minimal_construction():
    res = IntentResolution(
        data_use="essential.service",
        data_categories=["user.contact.email"],
        data_subject="customer",
        purpose_source=PurposeSource.DECLARED,
        chat_context_used=False,
        confidence=1.0,
        rationale="",
        source="fallback",
        model=None,
        tool_capability_profile_hash="abc123",
        scrubbed_args_hash="def456",
    )
    assert res.data_use == "essential.service"
    assert res.purpose_source == PurposeSource.DECLARED
    assert res.confidence == 1.0


def test_intent_resolution_confidence_clamped():
    # Confidence values outside [0,1] should raise on construction
    import pytest
    with pytest.raises(ValueError):
        IntentResolution(
            data_use="x",
            data_categories=[],
            data_subject=None,
            purpose_source=PurposeSource.INFERRED,
            chat_context_used=False,
            confidence=1.5,
            rationale="",
            source="inference",
            model="claude-haiku-4-5",
            tool_capability_profile_hash="",
            scrubbed_args_hash="",
        )


def test_consumer_modes_enum_values():
    assert ConsumerMode.AGENT.value == "agent"
    assert ConsumerMode.INTERACTIVE.value == "interactive"


def test_decision_outcomes_enum_values():
    assert DecisionOutcome.ALLOW.value == "ALLOW"
    assert DecisionOutcome.DENY.value == "DENY"
    assert DecisionOutcome.NO_DECISION.value == "NO_DECISION"


def test_chat_context_optional_fields():
    ctx = ChatContext(recent_user_messages=["hello"])
    assert ctx.recent_user_messages == ["hello"]
    assert ctx.conversation_summary is None
    assert ctx.active_user_intent is None


def test_consumer_requires_allowable_purpose_keys():
    c = Consumer(
        fides_key="acme_support",
        mode=ConsumerMode.AGENT,
        allowable_purpose_keys=["essential.service.operations.support"],
        chat_context_inference=False,
    )
    assert c.fides_key == "acme_support"
    assert len(c.allowable_purpose_keys) == 1


def test_evaluation_input_carries_consumer_and_resolution():
    ei = EvaluationInput(
        consumer_fides_key="acme_support",
        data_use="essential.service.operations.support",
        data_categories=["user.contact.email"],
        data_subject="customer",
        environment={"geo_location": "US-CA"},
    )
    assert ei.consumer_fides_key == "acme_support"


def test_registered_tool_carries_schema():
    rt = RegisteredTool(
        upstream_key="zendesk",
        tool_name="get_ticket",
        description="Fetch a Zendesk ticket by ID.",
        input_schema={"type": "object", "properties": {"id": {"type": "string"}}},
    )
    assert rt.tool_schema_hash != ""  # auto-computed sha256 of input_schema


def test_scrub_result_pairs_text_and_hash():
    sr = ScrubResult(scrubbed_text="email=<email>", scrubbed_hash="abc")
    assert sr.scrubbed_text == "email=<email>"
    assert sr.scrubbed_hash == "abc"


def test_capability_profile_field_set():
    cp = CapabilityProfile(
        upstream_key="zendesk",
        tool_name="get_ticket",
        tool_schema_hash="abc",
        plausible_data_categories=["user.contact.email", "user.name"],
        base_confidence=0.9,
        model_used="anthropic/claude-sonnet-4-6",
    )
    assert "user.contact.email" in cp.plausible_data_categories


def test_decision_envelope():
    d = Decision(
        decision=DecisionOutcome.ALLOW,
        decisive_policy_key="allow_support_access",
        action_message=None,
        evaluated_policies=[],
    )
    assert d.decision is DecisionOutcome.ALLOW
