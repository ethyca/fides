"""Intent resolver — dispatches on consumer.mode.

Public entry point: IntentResolver.resolve(...).

Strategies:
- Agent mode: data_use/data_subject are anchored to the consumer's declared
  purpose. Categories are inferred via Stage 2 (with cached Stage 1 profile).
- Interactive mode: per-call purpose selection from allowable_purpose_keys
  (Task 11).

Both strategies produce the same IntentResolution shape.
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from fides.service.mcp.intent.cache import IntentCache
from fides.service.mcp.intent.inference import InferenceClient
from fides.service.mcp.intent.prompts import (
    build_stage1_prompts,
    build_stage2_category_prompts,
)
from fides.service.mcp.models import (
    CapabilityProfile,
    ChatContext,
    Consumer,
    ConsumerMode,
    IntentResolution,
    IntentSource,
    PurposeSource,
    RegisteredTool,
)
from fides.service.mcp.scrub import Scrubber
from fides.service.mcp.taxonomy import TenantTaxonomy


class Stage1Output(BaseModel):
    plausible_data_categories: list[str]
    base_confidence: float = Field(ge=0.0, le=1.0)


class Stage2CategoryOutput(BaseModel):
    data_categories: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class IntentResolver:
    def __init__(
        self,
        *,
        inference: InferenceClient,
        cache: IntentCache,
        scrubber: Scrubber,
        taxonomy: TenantTaxonomy,
        purpose_data_uses: dict[str, str],
        purpose_data_subjects: dict[str, str | None],
        stage1_model: str | None = None,
        stage2_model: str | None = None,
        stage1_timeout_s: float = 15.0,
        stage2_timeout_s: float = 3.0,
    ) -> None:
        self._inference = inference
        self._cache = cache
        self._scrubber = scrubber
        self._taxonomy = taxonomy
        self._purpose_data_uses = purpose_data_uses
        self._purpose_data_subjects = purpose_data_subjects
        self._stage1_model = stage1_model
        self._stage2_model = stage2_model
        self._stage1_timeout = stage1_timeout_s
        self._stage2_timeout = stage2_timeout_s

    async def resolve(
        self,
        *,
        consumer: Consumer,
        tool: RegisteredTool,
        arguments: dict[str, Any],
        environment: dict[str, Any],
        purpose_hint: str | None = None,
        session_purpose: str | None = None,
        chat_context: ChatContext | None = None,
    ) -> IntentResolution:
        if consumer.mode is ConsumerMode.AGENT:
            return await self._resolve_agent(
                consumer, tool, arguments, purpose_hint=purpose_hint,
            )
        raise NotImplementedError("interactive mode lands in Task 11")

    async def _resolve_agent(
        self,
        consumer: Consumer,
        tool: RegisteredTool,
        arguments: dict[str, Any],
        *,
        purpose_hint: str | None,
    ) -> IntentResolution:
        # 1) Pick purpose
        if purpose_hint:
            if purpose_hint not in consumer.allowable_purpose_keys:
                raise ValueError(
                    f"purpose_hint {purpose_hint!r} not in consumer's allowable set"
                )
            chosen_purpose = purpose_hint
            purpose_source = PurposeSource.EXPLICIT_HINT
        else:
            if len(consumer.allowable_purpose_keys) != 1:
                raise ValueError(
                    "agent consumer with >1 allowable purposes requires a purpose_hint"
                )
            chosen_purpose = consumer.allowable_purpose_keys[0]
            purpose_source = PurposeSource.DECLARED

        data_use = self._purpose_data_uses.get(chosen_purpose, chosen_purpose)
        data_subject = self._purpose_data_subjects.get(chosen_purpose)

        # 2) Categories via Stage 2 (with Stage 1 capability profile)
        scrub = self._scrubber.scrub_dict(arguments)
        cached_resolution = self._cache.get_resolution(
            tool.upstream_key, tool.tool_name, scrub.scrubbed_hash
        )
        if cached_resolution is not None:
            return cached_resolution.model_copy(
                update={
                    "data_use": data_use,
                    "data_subject": data_subject,
                    "purpose_source": purpose_source,
                    "source": IntentSource.CACHE,
                }
            )

        profile = await self._get_or_build_profile(tool)
        stage2_sys, stage2_user = build_stage2_category_prompts(
            tool_name=tool.tool_name,
            tool_description=tool.description,
            capability_profile_json=profile.model_dump_json(),
            scrubbed_args_text=scrub.scrubbed_text,
            allowed_data_categories=profile.plausible_data_categories,
        )
        completion = await self._inference.complete_structured(
            system_prompt=stage2_sys,
            user_prompt=stage2_user,
            output_model=Stage2CategoryOutput,
            timeout_s=self._stage2_timeout,
            model=self._stage2_model,
        )
        narrowed = [
            c for c in completion.parsed.data_categories
            if self._taxonomy.is_known_data_category(c)
        ]
        resolution = IntentResolution(
            data_use=data_use,
            data_categories=narrowed,
            data_subject=data_subject,
            purpose_source=purpose_source,
            chat_context_used=False,
            confidence=completion.parsed.confidence,
            rationale=completion.parsed.rationale,
            source=IntentSource.INFERENCE,
            model=completion.model,
            tool_capability_profile_hash=tool.tool_schema_hash,
            scrubbed_args_hash=scrub.scrubbed_hash,
        )
        self._cache.put_resolution(
            tool.upstream_key, tool.tool_name, scrub.scrubbed_hash, resolution
        )
        return resolution

    async def _get_or_build_profile(self, tool: RegisteredTool) -> CapabilityProfile:
        cached = self._cache.get_profile(
            tool.upstream_key, tool.tool_name, tool.tool_schema_hash
        )
        if cached is not None:
            return cached
        sys_p, user_p = build_stage1_prompts(
            tool_name=tool.tool_name,
            tool_description=tool.description,
            tool_schema=tool.input_schema,
            allowed_data_categories=self._taxonomy.allowed_data_categories(),
        )
        completion = await self._inference.complete_structured(
            system_prompt="Stage1: " + sys_p,
            user_prompt=user_p,
            output_model=Stage1Output,
            timeout_s=self._stage1_timeout,
            model=self._stage1_model,
        )
        narrowed = [
            c for c in completion.parsed.plausible_data_categories
            if self._taxonomy.is_known_data_category(c)
        ]
        profile = CapabilityProfile(
            upstream_key=tool.upstream_key,
            tool_name=tool.tool_name,
            tool_schema_hash=tool.tool_schema_hash,
            plausible_data_categories=narrowed,
            base_confidence=completion.parsed.base_confidence,
            model_used=completion.model,
        )
        self._cache.put_profile(
            tool.upstream_key, tool.tool_name, tool.tool_schema_hash, profile
        )
        return profile
