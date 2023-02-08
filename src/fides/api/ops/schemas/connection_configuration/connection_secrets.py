from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra, root_validator

from fides.api.ops.models.connectionconfig import ConnectionTestStatus
from fides.api.ops.schemas import Msg


class ConnectionConfigSecretsSchema(BaseModel, abc.ABC):
    """Abstract Base Schema for updating Connection Configuration Secrets"""

    url: Optional[str] = None  # User can always specify the URL directly

    _required_components: List[str]

    def __init_subclass__(cls: BaseModel, **kwargs: Any):  # type: ignore
        super().__init_subclass__(**kwargs)  # type: ignore
        if not getattr(cls, "_required_components"):
            raise TypeError(f"Class {cls.__name__} must define '_required_components.'")  # type: ignore

    @root_validator
    @classmethod
    def required_components_supplied(  # type: ignore
        cls: ConnectionConfigSecretsSchema, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that the minimum required components have been supplied.

        Connection configurations either 1) need the entire URL
        *OR* 2) all of the required components to *build* that URL."""
        min_fields_present = values.get("url") or all(
            values.get(component) for component in cls._required_components
        )
        if not min_fields_present:
            raise ValueError(
                f"{cls.__name__} must be supplied a 'url' or all of: {cls._required_components}."  # type: ignore
            )

        return values

    class Config:
        """Only permit selected secret fields to be stored."""

        extra = Extra.forbid
        orm_mode = True


class TestStatusMessage(Msg):
    """A schema for checking status."""

    test_status: Optional[ConnectionTestStatus] = None
    failure_reason: Optional[str] = None
