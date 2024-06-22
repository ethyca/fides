from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, ClassVar

from pydantic import BaseModel, ConfigDict, model_validator

from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.schemas import Msg


class ConnectionConfigSecretsSchema(BaseModel, abc.ABC):
    """Abstract Base Schema for updating Connection Configuration Secrets"""

    # NOTE: any fields not listed in `_required_components` must also have an
    # annotated Optional type, in order to be treated effectively as optional fields
    _required_components: ClassVar[List[str]]

    def __init_subclass__(cls: BaseModel, **kwargs: Any):  # type: ignore
        super().__init_subclass__(**kwargs)  # type: ignore
        if not getattr(cls, "_required_components"):
            raise TypeError(f"Class {cls.__name__} must define '_required_components.'")  # type: ignore

    @model_validator(mode="after")
    def required_components_supplied(  # type: ignore
        self
    ) -> "ConnectionConfigSecretsSchema":
        """Validate that the minimum required components have been supplied."""
        min_fields_present = all(
            getattr(self, component) for component in self._required_components
        )
        if not min_fields_present:
            raise ValueError(
                f"{self.__name__} must be supplied all of: {self._required_components}."  # type: ignore
            )

        return self

    model_config = ConfigDict(extra="ignore", from_attributes=True)


class TestStatusMessage(Msg):
    """A schema for checking status."""

    test_status: Optional[ConnectionTestStatus] = None
    failure_reason: Optional[str] = None
