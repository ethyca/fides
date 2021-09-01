from typing import Optional

from pydantic import validator

from fideslang.models.fides_model import FidesModel, FidesKey
from fideslang.models.validation import no_self_reference


class DataUse(FidesModel):
    parentKey: Optional[FidesKey]

    _no_self_reference = validator("parentKey", allow_reuse=True)(no_self_reference)
