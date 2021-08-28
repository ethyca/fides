from typing import Optional

from fideslang.models.fides_model import FidesModel


class DataCategory(FidesModel):
    parentKey: Optional[str]  # TODO can't self-reference
