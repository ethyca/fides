import pytest
from pydantic import BaseModel

from fides.service.mcp.intent.cache import IntentCache
from fides.service.mcp.intent.resolver import IntentResolver, Stage2CategoryOutput
from fides.service.mcp.models import (
    ChatContext,
    Consumer,
    ConsumerMode,
    PurposeSource,
    RegisteredTool,
)
from fides.service.mcp.scrub import RegexScrubber
from fides.service.mcp.taxonomy import TenantTaxonomy


class _FakeInference:
    def __init__(self, stage1_categories, stage2_categories, stage2_confidence=0.95):
        self.stage1_categories = stage1_categories
        self.stage2_categories = stage2_categories
        self.stage2_confidence = stage2_confidence

    async def complete_structured(self, *, system_prompt, user_prompt, output_model, timeout_s, max_tokens=1024, model=None):
        from fides.service.mcp.intent.inference import StructuredCompletion
        if system_prompt.startswith("Stage1:"):
            return StructuredCompletion(
                parsed=output_model(
                    plausible_data_categories=self.stage1_categories,
                    base_confidence=0.9,
                ),
                model="claude-sonnet-4-6",
                raw_content="",
            )
        return StructuredCompletion(
            parsed=output_model(
                data_categories=self.stage2_categories,
                confidence=self.stage2_confidence,
                rationale="testing",
            ),
            model="claude-haiku-4-5",
            raw_content="",
        )


@pytest.mark.asyncio
async def test_agent_mode_single_purpose_uses_declared_purpose():
    consumer = Consumer(
        fides_key="acme",
        mode=ConsumerMode.AGENT,
        allowable_purpose_keys=["essential.service.operations.support"],
    )
    tool = RegisteredTool(
        upstream_key="zendesk",
        tool_name="get_ticket",
        description="Fetch a Zendesk ticket.",
        input_schema={"type": "object", "properties": {"id": {"type": "string"}}},
    )
    resolver = IntentResolver(
        inference=_FakeInference(
            stage1_categories=["user.contact.email"],
            stage2_categories=["user.contact.email"],
        ),
        cache=IntentCache(),
        scrubber=RegexScrubber(),
        taxonomy=TenantTaxonomy.from_fideslang_defaults(),
        purpose_data_uses={
            "essential.service.operations.support": "essential.service.operations.support",
        },
        purpose_data_subjects={"essential.service.operations.support": "customer"},
    )
    res = await resolver.resolve(
        consumer=consumer,
        tool=tool,
        arguments={"id": "abc"},
        environment={},
    )
    assert res.data_use == "essential.service.operations.support"
    assert res.data_subject == "customer"
    assert "user.contact.email" in res.data_categories
    assert res.purpose_source == PurposeSource.DECLARED
    assert res.chat_context_used is False


@pytest.mark.asyncio
async def test_agent_mode_explicit_hint_overrides_declared_when_multi():
    consumer = Consumer(
        fides_key="acme",
        mode=ConsumerMode.AGENT,
        allowable_purpose_keys=["a.b", "c.d"],
    )
    tool = RegisteredTool(
        upstream_key="x", tool_name="t", description="", input_schema={},
    )
    resolver = IntentResolver(
        inference=_FakeInference(["user.contact.email"], ["user.contact.email"]),
        cache=IntentCache(),
        scrubber=RegexScrubber(),
        taxonomy=TenantTaxonomy.from_fideslang_defaults(),
        purpose_data_uses={"a.b": "a.b", "c.d": "c.d"},
        purpose_data_subjects={"a.b": "customer", "c.d": "employee"},
    )
    res = await resolver.resolve(
        consumer=consumer, tool=tool, arguments={}, environment={},
        purpose_hint="c.d",
    )
    assert res.data_use == "c.d"
    assert res.data_subject == "employee"
    assert res.purpose_source == PurposeSource.EXPLICIT_HINT
