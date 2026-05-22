import pytest
from tests.service.mcp.intent.test_resolver_agent import _FakeInference  # reuse fake

from fides.service.mcp.intent.cache import IntentCache
from fides.service.mcp.intent.resolver import IntentResolver
from fides.service.mcp.models import (
    ChatContext,
    Consumer,
    ConsumerMode,
    PurposeSource,
    RegisteredTool,
)
from fides.service.mcp.scrub import RegexScrubber
from fides.service.mcp.taxonomy import TenantTaxonomy


class _PurposeFakeInference(_FakeInference):
    def __init__(self, stage1, stage2, purpose, purpose_conf=0.9):
        super().__init__(stage1, stage2)
        self.purpose = purpose
        self.purpose_conf = purpose_conf

    async def complete_structured(self, *, system_prompt, user_prompt, output_model, timeout_s, max_tokens=1024, model=None):
        from fides.service.mcp.intent.inference import StructuredCompletion
        if "purpose" in system_prompt.lower() and "selection" in system_prompt.lower():
            return StructuredCompletion(
                parsed=output_model(
                    selected_purpose=self.purpose,
                    confidence=self.purpose_conf,
                    rationale="testing",
                ),
                model="claude-haiku-4-5",
                raw_content="",
            )
        return await super().complete_structured(
            system_prompt=system_prompt, user_prompt=user_prompt,
            output_model=output_model, timeout_s=timeout_s, max_tokens=max_tokens,
            model=model,
        )


def _resolver(inference):
    return IntentResolver(
        inference=inference,
        cache=IntentCache(),
        scrubber=RegexScrubber(),
        taxonomy=TenantTaxonomy.from_fideslang_defaults(),
        purpose_data_uses={
            "essential.service.operations.support": "essential.service.operations.support",
            "analytics.reporting": "analytics.reporting",
        },
        purpose_data_subjects={
            "essential.service.operations.support": "customer",
            "analytics.reporting": "customer",
        },
    )


@pytest.mark.asyncio
async def test_interactive_single_allowable_purpose_skips_selection():
    consumer = Consumer(
        fides_key="claude_desktop",
        mode=ConsumerMode.INTERACTIVE,
        allowable_purpose_keys=["essential.service.operations.support"],
    )
    tool = RegisteredTool(
        upstream_key="zendesk", tool_name="get_ticket", description="",
        input_schema={"type": "object", "properties": {"id": {"type": "string"}}},
    )
    res = await _resolver(_FakeInference(["user.contact.email"], ["user.contact.email"])).resolve(
        consumer=consumer, tool=tool, arguments={"id": "abc"}, environment={},
    )
    assert res.data_use == "essential.service.operations.support"
    assert res.purpose_source == PurposeSource.DECLARED


@pytest.mark.asyncio
async def test_interactive_uses_purpose_hint_when_provided():
    consumer = Consumer(
        fides_key="claude_desktop",
        mode=ConsumerMode.INTERACTIVE,
        allowable_purpose_keys=["essential.service.operations.support", "analytics.reporting"],
    )
    tool = RegisteredTool(upstream_key="z", tool_name="t", description="", input_schema={})
    res = await _resolver(_FakeInference([], [])).resolve(
        consumer=consumer, tool=tool, arguments={}, environment={},
        purpose_hint="analytics.reporting",
    )
    assert res.data_use == "analytics.reporting"
    assert res.purpose_source == PurposeSource.EXPLICIT_HINT


@pytest.mark.asyncio
async def test_interactive_session_purpose_when_no_hint():
    consumer = Consumer(
        fides_key="claude_desktop",
        mode=ConsumerMode.INTERACTIVE,
        allowable_purpose_keys=["essential.service.operations.support", "analytics.reporting"],
    )
    tool = RegisteredTool(upstream_key="z", tool_name="t", description="", input_schema={})
    res = await _resolver(_FakeInference([], [])).resolve(
        consumer=consumer, tool=tool, arguments={}, environment={},
        session_purpose="analytics.reporting",
    )
    assert res.data_use == "analytics.reporting"
    assert res.purpose_source == PurposeSource.SESSION


@pytest.mark.asyncio
async def test_interactive_inference_picks_from_allowable_set_with_chat():
    consumer = Consumer(
        fides_key="claude_desktop",
        mode=ConsumerMode.INTERACTIVE,
        allowable_purpose_keys=["essential.service.operations.support", "analytics.reporting"],
        chat_context_inference=True,
    )
    tool = RegisteredTool(
        upstream_key="zendesk", tool_name="get_ticket", description="",
        input_schema={"type": "object", "properties": {"id": {"type": "string"}}},
    )
    res = await _resolver(
        _PurposeFakeInference(
            stage1=["user.contact.email"],
            stage2=["user.contact.email"],
            purpose="essential.service.operations.support",
            purpose_conf=0.9,
        )
    ).resolve(
        consumer=consumer, tool=tool, arguments={"id": "abc"}, environment={},
        chat_context=ChatContext(recent_user_messages=["check my support ticket"]),
    )
    assert res.data_use == "essential.service.operations.support"
    assert res.purpose_source == PurposeSource.INFERRED
    assert res.chat_context_used is True
