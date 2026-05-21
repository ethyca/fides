"""Prompt builders for the two-stage intent resolver.

Each builder returns (system_prompt, user_prompt). The user prompt contains
a `[[ CACHE_CONTROL ]]` marker (handled by litellm's prompt-caching layer when
running against Anthropic via OpenRouter) so the static prefix is cacheable.

These prompts intentionally constrain output vocabularies to the caller's
allowed sets and require JSON output that matches Pydantic models defined
in resolver.py.
"""

from __future__ import annotations

import json

STAGE1_SYSTEM = (
    "You are a privacy-classification assistant. Given an MCP tool's name, "
    "description, and inputSchema, output the superset of fideslang "
    "data categories the tool could plausibly access in any invocation. "
    "Respond ONLY with valid JSON matching: "
    '{"plausible_data_categories": [...fides_keys...], "base_confidence": float between 0 and 1}. '
    "Use only the data categories listed in the allowed set."
)

STAGE2_CATEGORY_SYSTEM = (
    "You are a privacy-classification assistant. Given an MCP tool, its capability "
    "profile (superset of plausible categories), and the scrubbed arguments of a "
    "specific call, narrow the categories to the minimal set THIS call touches. "
    "Respond ONLY with valid JSON matching: "
    '{"data_categories": [...fides_keys...], "confidence": float, "rationale": "short string"}. '
    "Use only the data categories listed in the allowed set."
)

STAGE2_PURPOSE_SYSTEM = (
    "You are a privacy-purpose-selection assistant. Given an MCP tool call and "
    "the consumer's set of allowable purposes (fideslang data_use keys), pick the "
    "ONE purpose this specific call is serving. Use the chat context when present "
    "as the primary signal. Respond ONLY with valid JSON: "
    '{"selected_purpose": "<one of allowable>", "confidence": float, "rationale": "short string"}.'
)

CACHE_MARK = "[[ CACHE_CONTROL ]]"


def build_stage1_prompts(
    *,
    tool_name: str,
    tool_description: str,
    tool_schema: dict,
    allowed_data_categories: list[str],
) -> tuple[str, str]:
    user = (
        f"Tool name: {tool_name}\n"
        f"Description: {tool_description}\n"
        f"InputSchema:\n{json.dumps(tool_schema, indent=2)}\n"
        f"Allowed data categories:\n{json.dumps(sorted(allowed_data_categories))}\n"
        f"{CACHE_MARK}\n"
    )
    return STAGE1_SYSTEM, user


def build_stage2_category_prompts(
    *,
    tool_name: str,
    tool_description: str,
    capability_profile_json: str,
    scrubbed_args_text: str,
    allowed_data_categories: list[str],
    chat_context_text: str | None = None,
) -> tuple[str, str]:
    static_prefix = (
        f"Tool: {tool_name}\n"
        f"Description: {tool_description}\n"
        f"Capability profile: {capability_profile_json}\n"
        f"Allowed data categories: {json.dumps(sorted(allowed_data_categories))}\n"
        f"{CACHE_MARK}\n"
    )
    dynamic = f"<arguments>{scrubbed_args_text}</arguments>\n"
    if chat_context_text:
        dynamic += f"<chat>{chat_context_text}</chat>\n"
    return STAGE2_CATEGORY_SYSTEM, static_prefix + dynamic


def build_stage2_purpose_prompts(
    *,
    tool_name: str,
    scrubbed_args_text: str,
    allowable_purpose_keys: list[str],
    chat_context_text: str | None = None,
) -> tuple[str, str]:
    user = (
        f"Tool: {tool_name}\n"
        f"Allowable purposes: {json.dumps(sorted(allowable_purpose_keys))}\n"
        f"{CACHE_MARK}\n"
        f"<arguments>{scrubbed_args_text}</arguments>\n"
    )
    if chat_context_text:
        user += f"<chat>{chat_context_text}</chat>\n"
    return STAGE2_PURPOSE_SYSTEM, user
