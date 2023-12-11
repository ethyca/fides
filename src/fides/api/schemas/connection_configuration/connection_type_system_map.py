from typing import List, Optional, Union

from pydantic import BaseModel

from fides.api.models.connectionconfig import ConnectionType
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.api.schemas.policy import ActionType


class ConnectionSystemTypeMap(BaseModel):
    """
    Describes the returned schema for connection types
    """

    identifier: Union[ConnectionType, str]
    type: SystemType
    human_readable: str
    encoded_icon: Optional[str]
    authorization_required: Optional[bool] = False
    user_guide: Optional[str]
    supported_actions: List[ActionType]

    class Config:
        """Use enum values and set orm mode"""

        use_enum_values = True
        orm_mode = True
