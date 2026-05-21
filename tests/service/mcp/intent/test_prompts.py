from fides.service.mcp.intent.prompts import (
    build_stage1_prompts,
    build_stage2_category_prompts,
    build_stage2_purpose_prompts,
)


def test_stage1_includes_tool_schema_and_taxonomy():
    sys, user = build_stage1_prompts(
        tool_name="get_ticket",
        tool_description="Fetch a Zendesk ticket by ID.",
        tool_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        allowed_data_categories=["user.contact.email", "user.name"],
    )
    assert "get_ticket" in user
    assert "user.contact.email" in user
    assert "[[ CACHE_CONTROL ]]" in user  # cache marker present in static prefix


def test_stage2_category_includes_scrubbed_args():
    sys, user = build_stage2_category_prompts(
        tool_name="get_ticket",
        tool_description="Fetch a Zendesk ticket by ID.",
        capability_profile_json='{"plausible_data_categories": ["user.contact.email"]}',
        scrubbed_args_text='{"id": "abc"}',
        allowed_data_categories=["user.contact.email"],
    )
    assert "user.contact.email" in user
    assert '"id": "abc"' in user
    assert "[[ CACHE_CONTROL ]]" in user


def test_stage2_purpose_constrained_to_allowable_set():
    sys, user = build_stage2_purpose_prompts(
        tool_name="get_ticket",
        scrubbed_args_text='{"id": "abc"}',
        allowable_purpose_keys=["essential.service.operations.support", "analytics.reporting"],
        chat_context_text="user said: I want to check on my ticket",
    )
    assert "essential.service.operations.support" in user
    assert "analytics.reporting" in user
    assert "I want to check on my ticket" in user
