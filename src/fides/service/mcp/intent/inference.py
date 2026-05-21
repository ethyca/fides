"""Inference client Protocol for MCP intent resolution.

Fides OSS defines the contract; the concrete litellm-backed implementation
lives in Fidesplus (`fidesplus/mcp_pdp_addons/inference.py`). Tests in Fides
use fake implementations that satisfy this Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Type, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class InferenceTimeout(TimeoutError):
    """Raised when an inference call exceeds its timeout budget."""


class InferenceError(RuntimeError):
    """Raised when an inference call fails (provider error, parse failure, etc.)."""


@dataclass
class StructuredCompletion[T: BaseModel]:
    parsed: T
    model: str
    raw_content: str


@runtime_checkable
class InferenceClient(Protocol):
    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: Type[T],
        timeout_s: float,
        max_tokens: int = 1024,
        model: str | None = None,
    ) -> StructuredCompletion[T]: ...
