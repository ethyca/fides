"""
User entity module - session-independent domain objects for user operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.user import DisabledReason


class UserEntity(FidesSchema):
    """
    Domain entity for FidesUser, decoupled from SQLAlchemy ORM.

    Pydantic model, session-independent and can be freely passed around,
    serialized, and cached. Provides automatic validation and JSON serialization.

    Usage:
        entity = UserEntity.model_validate(orm_user)
    """

    id: str
    username: str
    email_address: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: bool = False
    disabled_reason: Optional[DisabledReason] = None
    password_login_enabled: Optional[bool] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None

    @property
    def is_deleted(self) -> bool:
        """Check if the user has been soft-deleted."""
        return self.deleted_at is not None
