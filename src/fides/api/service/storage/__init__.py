# Storage service modules
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.dsr_storage import (
    stream_html_dsr_report_to_storage_multipart,
)

# Provider-specific implementations
from fides.api.service.storage.streaming.s3.s3_storage_client import (
    S3StorageClient,
    create_s3_storage_client,
)

# Legacy S3 streaming interface (maintains backward compatibility)
from fides.api.service.storage.streaming.s3.streaming_s3 import upload_to_s3_streaming
from fides.api.service.storage.streaming.schemas import (
    MultipartUploadResponse,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.storage_client_factory import (
    CloudStorageClientFactory,
    get_storage_client,
)
from fides.api.service.storage.streaming.streaming_storage import StreamingStorage

__all__ = [
    # Core abstractions
    "CloudStorageClient",
    "CloudStorageClientFactory",
    "get_storage_client",
    # Cloud-agnostic streaming
    "StreamingStorage",
    # DSR-specific storage operations
    "stream_html_dsr_report_to_storage_multipart",
    # Data schemas
    "MultipartUploadResponse",
    "UploadPartResponse",
    # Provider implementations
    "S3StorageClient",
    "create_s3_storage_client",
    # S3 streaming interface
    "upload_to_s3_streaming",
]
