from typing import List, Optional

from pydantic import field_validator

from fides.api.schemas.base_class import FidesSchema


class ClientCreatedResponse(FidesSchema):
    """Response schema for client creation"""

    client_id: str
    client_secret: str


class ClientCreateRequest(FidesSchema):
    """Request schema for creating an OAuth client"""

    name: Optional[str] = None
    description: Optional[str] = None
    scopes: List[str] = []

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name must not be empty")
        return v


class ClientUpdateRequest(FidesSchema):
    """Request schema for updating an OAuth client. All fields are optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name must not be empty")
        return v


class ClientResponse(FidesSchema):
    """Response schema for an OAuth client. Never includes the client secret."""

    client_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: List[str] = []


class ClientSecretRotateResponse(FidesSchema):
    """Response schema for secret rotation. Secret is shown exactly once."""

    client_id: str
    client_secret: str
