# Storage service modules
from fides.api.service.storage.streaming.cloud_storage_client import (
    CloudStorageClient,
    ProgressCallback,
)
from fides.api.service.storage.streaming.dsr_storage import (
    stream_html_dsr_report_to_storage_multipart,
)

# GCS storage client - basic implementation only, streaming not yet available
from fides.api.service.storage.streaming.gcs.gcs_storage_client import (
    GCSStorageClient,
    create_gcs_storage_client,
)

# Provider-specific implementations
from fides.api.service.storage.streaming.s3.s3_storage_client import (
    S3StorageClient,
    create_s3_storage_client,
)

# Legacy S3 streaming interface (maintains backward compatibility)
from fides.api.service.storage.streaming.s3.streaming_s3 import (
    upload_to_s3_streaming,
    upload_to_s3_streaming_advanced,
)
from fides.api.service.storage.streaming.schemas import (
    MultipartUploadResponse,
    ProcessingMetrics,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.storage_client_factory import (
    CloudStorageClientFactory,
    get_storage_client,
)
from fides.api.service.storage.streaming.streaming_storage import (
    upload_to_storage_streaming,
)

__all__ = [
    # Core abstractions
    "CloudStorageClient",
    "ProgressCallback",
    "CloudStorageClientFactory",
    "get_storage_client",
    # Cloud-agnostic streaming
    "upload_to_storage_streaming",
    # DSR-specific storage operations
    "stream_html_dsr_report_to_storage_multipart",
    # Data schemas
    "ProcessingMetrics",
    "MultipartUploadResponse",
    "UploadPartResponse",
    # Provider implementations
    "S3StorageClient",
    "create_s3_storage_client",
    # GCS basic client - streaming implementation not yet available
    "GCSStorageClient",
    "create_gcs_storage_client",
    # Legacy S3 interface
    "upload_to_s3_streaming",
    "upload_to_s3_streaming_advanced",
]
