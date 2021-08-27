from typing import Optional

from fidesctl.lang.models.fides_model import FidesModel


class Registry(FidesModel):
    organizationId: int
    name: str
    description: str
