from typing import Optional

from pydantic import BaseModel


class MaskingAPIResponse(BaseModel):
    """The API Response returned upon masking completion"""

    plain: str
    masked_value: Optional[str]
