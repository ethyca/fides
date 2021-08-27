from typing import Optional

from fidesctl.lang.models.fides_model import FidesModel


class DataSubject(FidesModel):
    organizationId: int = 1
    name: str
    description: Optional[str]
