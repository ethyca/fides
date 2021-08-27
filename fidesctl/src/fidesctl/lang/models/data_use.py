from typing import Optional

from fidesctl.lang.models.fides_model import FidesModel


class DataUse(FidesModel):
    id: Optional[int]
    organizationId: int = 1
    fidesKey: str
    name: str
    parentKey: Optional[str]
    description: str
