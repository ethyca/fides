import re
from typing import List

from pydantic import BaseModel, Field, field_validator


class PrivacyRequestRedactionPatternsRequest(BaseModel):
    """Request schema for updating privacy request redaction patterns."""

    patterns: List[str] = Field(
        description="List of regex patterns used to redact dataset, collection, and field names in privacy request package reports",
        max_length=100,  # Limit number of patterns
    )

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, patterns: List[str]) -> List[str]:
        """Validate regex patterns with ReDoS protection via Pydantic's default rust-regex engine."""
        if not patterns:
            return patterns

        validated_patterns = []
        for i, pattern in enumerate(patterns):
            if not isinstance(pattern, str):
                raise ValueError(f"Pattern at index {i} must be a string")

            pattern = pattern.strip()
            if not pattern:
                raise ValueError(f"Pattern at index {i} cannot be empty")

            # Reasonable length limit for regex patterns
            if len(pattern) > 500:
                raise ValueError(
                    f"Pattern at index {i} is too long (max 500 characters)"
                )

            # Pydantic's rust-regex engine provides ReDoS protection
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern at index {i}: {e}")

            validated_patterns.append(pattern)

        return validated_patterns


class PrivacyRequestRedactionPatternsResponse(BaseModel):
    """Response schema for privacy request redaction patterns."""

    patterns: List[str] = Field(
        description="List of regex patterns used to redact dataset, collection, and field names in privacy request package reports"
    )

    model_config = {"from_attributes": True}
