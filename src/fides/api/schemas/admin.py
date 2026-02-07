"""Schemas for admin endpoints."""

from pydantic import BaseModel, Field


class BackfillRequest(BaseModel):
    """Request body for triggering a database backfill operation."""

    batch_size: int = Field(
        default=5000,
        ge=100,
        le=50000,
        description="Number of rows to update per batch (default: 5000)",
    )
    batch_delay_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between batches in seconds (default: 1.0)",
    )


class BackfillStatusResponse(BaseModel):
    """Response body for backfill status endpoint."""

    is_running: bool = Field(
        description="Whether a backfill is currently running"
    )
    pending_count: dict[str, int] = Field(
        description="Count of rows pending backfill, keyed by backfill task name"
    )
