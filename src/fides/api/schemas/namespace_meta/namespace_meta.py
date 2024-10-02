from abc import ABC

from pydantic import BaseModel


class NamespaceMeta(BaseModel, ABC):
    pass
