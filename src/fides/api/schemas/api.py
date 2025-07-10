from typing import Any, Dict

from pydantic import BaseModel


class BulkResponse(BaseModel):
    """
    Schema for responses from bulk update/create requests.  Override to set "succeeded" and "failed" attributes on
    your child class with paginated types.

    Example:
    from fastapi_pagination import Page

    succeeded: List[ConnectionConfigurationResponse]
    failed: List[BulkUpdateFailed]
    """

    @classmethod
    def __pydantic_init_subclass__(cls: BaseModel, **kwargs):  # type: ignore
        super().__pydantic_init_subclass__(**kwargs)  # type: ignore
        if "succeeded" not in cls.model_fields or "failed" not in cls.model_fields:
            raise TypeError(
                f"Class {cls.__name__} needs both 'succeeded' and 'failed' attributes defined."  # type: ignore
            )


class ResponseWithMessage(BaseModel):
    """Generic schema for responses with a message"""

    message: str


class BulkUpdateFailed(BaseModel):
    """Schema for use when Bulk Create/Update fails."""

    message: str
    data: Dict[str, Any]
