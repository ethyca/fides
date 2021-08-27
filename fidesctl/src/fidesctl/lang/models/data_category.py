from typing import Optional

from fidesctl.lang.models.fides_model import FidesModel


class DataCategory(FidesModel):
    organizationId: int = 1
    name: str
    parentKey: Optional[str]
    description: str
