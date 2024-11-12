from abc import ABC

from pydantic import BaseModel

from fides.api.models.connectionconfig import ConnectionType


class NamespaceMeta(BaseModel, ABC):
    connection_type: ConnectionType
