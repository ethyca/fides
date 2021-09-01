from enum import Enum
from typing import List

from pydantic import BaseModel


class StatusEnum(str, Enum):
    FAIL = "FAIL"
    PASS = "PASS"


class Evaluation(BaseModel):

    status: StatusEnum = StatusEnum.PASS
    details: List[str]
    message: str = ""
