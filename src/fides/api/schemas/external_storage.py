"""Schema for external storage metadata."""

from typing import Optional

from pydantic import Field

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.storage.storage import StorageType


class ExternalStorageMetadata(FidesSchema):
    """Metadata for externally stored encrypted data."""

    storage_type: StorageType
    file_key: str = Field(description="Path/key of the file in external storage")
    filesize: int = Field(description="Size of the stored file in bytes", ge=0)
    storage_key: Optional[str] = Field(
        default=None, description="Storage configuration key used"
    )

    class Config:
        use_enum_values = True
