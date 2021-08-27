from typing import Optional

from fidesctl.lang.models.fides_model import FidesModel


class DataQualifier(FidesModel):
    id: Optional[int]
    organizationId: int = 1
    fidesKey: str
    name: str
    description: str
