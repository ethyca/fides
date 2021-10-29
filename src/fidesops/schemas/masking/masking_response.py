from pydantic import BaseModel


class MaskingAPIResponse(BaseModel):
    """The API Response returned upon masking completion"""

    plain: str
    masked_value: str
