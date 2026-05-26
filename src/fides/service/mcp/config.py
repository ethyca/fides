"""MCP shared-core settings.

Read via env vars prefixed FIDES__MCP__ (matching the existing Fides settings
pattern). The OpenRouter / LLM provider credentials are sourced from the
existing Fides LLMSettings (added in Task 1).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FIDES__MCP__", extra="ignore")

    pdp_enabled: bool = False
    # Model identifiers use the litellm `openrouter/` prefix so calls route
    # through OpenRouter (which holds the API key) rather than being
    # interpreted by litellm as direct Anthropic API calls.
    stage1_model: str = "openrouter/anthropic/claude-sonnet-4.6"
    stage2_model: str = "openrouter/anthropic/claude-haiku-4.5"
    stage1_timeout_s: float = 15.0
    stage2_timeout_s: float = 3.0

    category_confidence_floor: float = Field(default=0.7, ge=0.0, le=1.0)
    purpose_confidence_floor: float = Field(default=0.6, ge=0.0, le=1.0)

    no_decision_default: str = "DENY"  # or "ALLOW" for dev mode
