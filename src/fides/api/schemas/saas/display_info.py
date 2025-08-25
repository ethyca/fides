from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from fides.api.schemas.enums.connection_category import ConnectionCategory
from fides.api.schemas.enums.integration_feature import IntegrationFeature


class SaaSDisplayInfo(BaseModel):
    """
    Optional display information for SAAS integrations to enhance frontend presentation.
    When not provided, smart defaults will be inferred based on the integration type.
    """

    category: Optional[ConnectionCategory] = None
    tags: Optional[List[str]] = None
    enabled_features: Optional[List[IntegrationFeature]] = None

    model_config = ConfigDict(use_enum_values=True)
