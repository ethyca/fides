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

    def __init_subclass__(cls: BaseModel, **kwargs: Any):  # type: ignore
        super().__init_subclass__(**kwargs)  # type: ignore
        if "succeeded" not in cls.__fields__ or "failed" not in cls.__fields__:
            raise TypeError(
                f"Class {cls.__name__} needs both 'succeeded' and 'failed' attributes defined."  # type: ignore
            )


class BulkUpdateFailed(BaseModel):
    """Schema for use when Bulk Create/Update fails."""

    message: str
    data: Dict[str, Any]
