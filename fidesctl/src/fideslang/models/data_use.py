from typing import Optional

from fideslang.models.fides_model import FidesModel


class DataUse(FidesModel):
    parentKey: Optional[str]
