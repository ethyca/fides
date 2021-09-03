from enum import Enum
from typing import List

from pydantic import BaseModel


class EvaluationError(Exception):
    """Custom exception for when an Evaluation fails."""

    def __init__(self) -> None:
        super().__init__("Evaluation failed!")


class StatusEnum(str, Enum):
    FAIL = "FAIL"
    PASS = "PASS"


class Evaluation(BaseModel):

    status: StatusEnum = StatusEnum.PASS
    details: List[str]
    message: str = ""
