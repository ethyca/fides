from typing import Optional

from fidesctl.lang.models.fides_model import FidesModel


class DataSubject(FidesModel):
    id: Optional[int]
    organizationId: int = 1
    fidesKey: str
    name: str
    description: Optional[str]
