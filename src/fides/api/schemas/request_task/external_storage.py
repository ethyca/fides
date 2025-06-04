from typing import Optional

from pydantic import Field

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.storage.storage import StorageType


class ExternalStorageMetadata(FidesSchema):
    """Metadata for externally stored request task data"""

    storage_type: StorageType
    url: str = Field(description="URL or path to retrieve the external data")
    filesize: int = Field(description="Size of the stored file in bytes", ge=0)
    storage_key: Optional[str] = Field(
        default=None, description="Storage configuration key used"
    )

    class Config:
        use_enum_values = True
