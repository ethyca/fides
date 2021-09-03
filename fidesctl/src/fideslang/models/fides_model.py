import re
from typing import Optional, Pattern

from pydantic import BaseModel, ConstrainedStr


class FidesValidationError(Exception):
    """Custom exception for when the pydantic ValidationError can't be used."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FidesKey(ConstrainedStr):
    """
    A FidesKey should only contain alphanumeric characters or '_'
    """

    regex: Pattern[str] = re.compile(r"^[a-zA-Z0-9_]+$")

    @classmethod  # This overrides the default method to throw the custom FidesValidationError
    def validate(cls, value: str) -> str:
        if not cls.regex.match(value):
            raise FidesValidationError(
                "FidesKey must only contain alphanumeric characters or '_'."
            )

        return value


class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    id: Optional[int]
    organizationId: int = 1
    name: str
    description: Optional[str]
    fidesKey: FidesKey

    class Config:
        extra = "ignore"
