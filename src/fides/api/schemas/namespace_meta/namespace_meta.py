from abc import ABC
from typing import Optional

from pydantic import BaseModel


class NamespaceMeta(BaseModel, ABC):
    connection_type: Optional[str] = None
