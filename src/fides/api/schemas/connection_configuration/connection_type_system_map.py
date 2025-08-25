from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict

from fides.api.models.connectionconfig import ConnectionType
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.api.schemas.enums.connection_category import ConnectionCategory
from fides.api.schemas.enums.integration_feature import IntegrationFeature
from fides.api.schemas.policy import ActionType


class ConnectionSystemTypeMap(BaseModel):
    """
    Describes the returned schema for connection types
    """

    identifier: Union[ConnectionType, str]
    type: SystemType
    human_readable: str
    encoded_icon: Optional[str] = None
    authorization_required: Optional[bool] = False
    user_guide: Optional[str] = None
    supported_actions: List[ActionType]
    # New fields for enhanced display information
    category: Optional[ConnectionCategory] = None
    tags: Optional[List[str]] = None
    enabled_features: Optional[List[IntegrationFeature]] = None
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)
