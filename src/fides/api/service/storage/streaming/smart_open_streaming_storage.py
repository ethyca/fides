# pylint: disable=too-many-lines
from __future__ import annotations

import csv
import json
import time
from copy import deepcopy
from datetime import datetime
from io import BytesIO, StringIO
from itertools import chain
from typing import Any, Generator, Iterable, Optional, Tuple
from urllib.parse import unquote, urlparse

from fideslang.validation import AnyHttpUrlString
from loguru import logger
from stream_zip import _ZIP_32_TYPE, stream_zip

from fides.api.common_exceptions import StorageUploadError
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSRReportBuilder,
)
from fides.api.service.storage.streaming.dsr_storage import (
    create_dsr_report_files_generator,
    stream_dsr_buffer_to_storage,
)
from fides.api.service.storage.streaming.retry import retry_cloud_storage_operation
from fides.api.service.storage.streaming.schemas import (
    DEFAULT_CHUNK_SIZE,
    MAX_FILE_SIZE,
    AttachmentInfo,
    AttachmentProcessingInfo,
    SmartOpenStreamingStorageConfig,
    StorageUploadConfig,
    StreamingBufferConfig,
)
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient
from fides.api.service.storage.util import (
    determine_dataset_name_from_path,
    get_unique_filename,
    process_attachments_contextually,
    resolve_attachment_storage_path,
    resolve_path_from_context,
)

DEFAULT_ATTACHMENT_NAME = "attachment"
DEFAULT_FILE_MODE = 0o644
S3_AMAZONAWS_COM_DOMAIN = ".s3.amazonaws.com"


class SmartOpenStreamingStorage:
    """Streaming storage implementation using smart-open for efficient cloud-to-cloud data streaming.

    This class maintains our DSR-specific business logic (package splitting, attachment processing)
    while leveraging smart-open's mature streaming capabilities for storage operations.

    Key streaming features:
    - Data files (JSON/CSV): Small files loaded into memory for ZIP creation
    - Attachment files: Streamed in chunks (8KB) without loading entire files to memory
    - ZIP creation: Uses stream_zip for memory-efficient ZIP generation
    - Upload: Streams ZIP chunks directly to destination storage

    This ensures true cloud-to-cloud streaming with minimal memory usage and no local file storage.
    """

    def __init__(
        self,
        storage_client: SmartOpenStorageClient,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """Initialize with a smart-open storage client.

        Args:
            storage_client: Smart-open based storage client
            chunk_size: Size of chunks for streaming attachments (default: 5MB)

        Raises:
            ValidationError: If chunk_size is outside valid range (1KB - 2GB)
        """
        # Validate parameters using Pydantic schema
        config = SmartOpenStreamingStorageConfig(chunk_size=chunk_size)

        self.storage_client = storage_client
        self.chunk_size = config.chunk_size
        # Track used filenames per dataset to match DSR report builder behavior
        # Maps dataset_name -> set of used filenames
        self.used_filenames_per_dataset: dict[str, set[str]] = {}

    def _parse_storage_url(self, storage_key: str) -> tuple[str, str]:
        """Parse storage URL and return (bucket, key).

        Supports multiple URL formats:
        - s3://bucket/path
        - https://bucket.s3.amazonaws.com/path
        - http://bucket.s3.amazonaws.com/path
        - Generic HTTP(S) URLs (returns domain as bucket, path as key)

        Args:
            storage_key: Storage key or URL

        Returns:
            Tuple of (bucket_name, object_key)

        Raises:
            ValueError: If URL cannot be parsed
        """
        if storage_key is None or storage_key == "":
            logger.error(f"Storage key cannot be empty: {storage_key}")
            raise ValueError("Storage key cannot be empty")

        if storage_key.startswith("s3://"):
            # Extract bucket from S3 URL: s3://bucket/path
            parts = storage_key.split("/")
            if len(parts) < 4:
                logger.error(f"Invalid S3 URL format: {storage_key}")
                raise ValueError(f"Invalid S3 URL format: {storage_key}")
            return parts[2], "/".join(parts[3:])

        if S3_AMAZONAWS_COM_DOMAIN in storage_key:
            # Extract bucket and key from HTTP(S) S3 URL
            clean_url = storage_key.split("?")[0]
            parts = clean_url.split(S3_AMAZONAWS_COM_DOMAIN)
            if len(parts) == 2:
                bucket = parts[0].replace("https://", "").replace("http://", "")
                key = unquote(
                    parts[1].lstrip("/")
                )  # URL-decode and strip leading slash for S3 compatibility
                return bucket, key

        # Handle generic HTTP(S) URLs
        if storage_key.startswith(("http://", "https://")):
            parsed = urlparse(storage_key)
            bucket = parsed.netloc
            key = unquote(parsed.path.lstrip("/"))  # URL-decode the path
            return bucket, key

        raise ValueError(f"Could not parse storage URL: {storage_key}")

    def _convert_to_stream_zip_format(
        self, generator: Generator[Tuple[str, BytesIO, dict[str, Any]], None, None]
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Convert generator from (filename, BytesIO, metadata) to (filename, datetime, mode, method, content_iter) format.

        This adapter converts our internal generator format to the format expected by stream_zip.
        For data files, we can read the entire content since they're typically small JSON/CSV files.
        """
        for filename, content, _ in generator:
            # Reset BytesIO position and get content
            content.seek(0)
            content_bytes = content.read()
            content.seek(0)  # Reset for potential reuse

            yield filename, datetime.now(), DEFAULT_FILE_MODE, _ZIP_32_TYPE(), iter(
                [content_bytes]
            )

    def _validate_attachment(
        self, attachment: dict
    ) -> Optional[AttachmentProcessingInfo]:
        """Validate a single attachment and create AttachmentProcessingInfo.

        Args:
            attachment: Raw attachment data dictionary

        Returns:
            AttachmentProcessingInfo if valid, None otherwise
        """
        try:
            # Extract storage key using shared utility
            storage_key = (
                attachment.get("download_url") or attachment.get("file_name") or ""
            )
            if not storage_key:
                return None

            # Create AttachmentInfo
            attachment_info = AttachmentInfo(
                storage_key=storage_key,
                file_name=attachment.get("file_name"),
                size=attachment.get("size"),
                content_type=attachment.get("content_type"),
            )

            # Resolve base path using shared utility
            base_path = resolve_path_from_context(attachment)

            # Create AttachmentProcessingInfo
            processing_info = AttachmentProcessingInfo(
                attachment=attachment_info,
                base_path=base_path,
                item=attachment,
            )

            return processing_info

        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Failed to validate attachment: {attachment}, error: {e}")
            return None

    def _create_attachment_content_stream(
        self, bucket: str, key: str, storage_key: str
    ) -> Iterable[bytes]:
        """Create a streaming iterator for attachment content without loading entire file to memory.

        Args:
            bucket: Source bucket name
            key: Source key/path
            storage_key: Original storage key for logging

        Returns:
            Iterator that yields chunks of the attachment content
        """
        for arg in [bucket, key, storage_key]:
            if arg is None or arg == "":
                logger.error(f"{arg} cannot be empty: {arg}")
                raise ValueError(f"{arg} cannot be empty")

        try:
            with self.storage_client.stream_read(bucket, key) as content_stream:
                # Stream in chunks instead of reading entire file
                chunk_count = total_bytes = 0
                max_chunks = (
                    MAX_FILE_SIZE // self.chunk_size + 1
                )  # Safety limit to prevent infinite loops

                size_based_timeout = MAX_FILE_SIZE // (10 * 1024 * 1024)  # 1s per 10MB
                timeout = 300 + size_based_timeout  # 5 minutes base + 1s per 10MB
                start_time = time.time()

                # Log the calculated timeout for debugging
                logger.debug(
                    f"Starting stream for {storage_key} with timeout: {timeout}s "
                    f"(base: 300s + size-based: {size_based_timeout}s)"
                )

                while chunk_count < max_chunks and total_bytes < MAX_FILE_SIZE:
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= timeout:
                        raise TimeoutError(
                            f"Timeout reached ({timeout}s) while streaming attachment {storage_key}."
                        )

                    try:
                        chunk = content_stream.read(self.chunk_size)
                    except Exception as read_error:
                        logger.error(
                            f"Error reading chunk from stream for {storage_key}: {read_error}"
                        )
                        raise StorageUploadError(
                            f"Stream read error for {storage_key}: {read_error}"
                        ) from read_error

                    if not chunk:
                        # End of stream reached normally
                        logger.debug(
                            f"Successfully streamed attachment {storage_key}: "
                            f"{total_bytes} bytes in {chunk_count} chunks"
                        )
                        break

                    chunk_count += 1
                    total_bytes += len(chunk)
                    yield chunk

                # Log if we hit limits
                if chunk_count >= max_chunks:
                    logger.warning(
                        f"Maximum chunk count ({max_chunks}) reached for attachment {storage_key}. "
                        f"Streamed {total_bytes} bytes. Stream may be incomplete."
                    )
                elif total_bytes >= MAX_FILE_SIZE:
                    logger.warning(
                        f"Maximum file size ({MAX_FILE_SIZE} bytes) reached for attachment {storage_key}. "
                        f"Streamed {total_bytes} bytes in {chunk_count} chunks. Stream may be incomplete."
                    )

        except Exception as e:
            logger.error(f"Failed to stream attachment {storage_key}: {e}")
            raise StorageUploadError(
                f"Failed to stream attachment {storage_key}: {e}"
            ) from e

    def _collect_and_validate_attachments(
        self,
        data: dict,
        used_filenames_data: set[str],
        used_filenames_attachments: set[str],
        processed_attachments: dict[tuple[str, str], str],
    ) -> list[AttachmentProcessingInfo]:
        """Collect and validate attachments using the same contextual approach as DSR report builder.

        This method uses the shared contextual processing logic to ensure consistency
        between DSR report builder and streaming storage.

        Args:
            data: The data dictionary containing items with attachments

        Returns:
            List of validated AttachmentProcessingInfo objects
        """
        validated_attachments = []

        # Use the shared contextual processing function
        # Note: This method should only be used when DSR report builder is not available
        # For HTML format, use _collect_and_validate_attachments_from_dsr_builder instead
        processed_attachments_list = process_attachments_contextually(
            data=data,
            used_filenames_data=used_filenames_data,
            used_filenames_attachments=used_filenames_attachments,
            processed_attachments=processed_attachments,
            enable_streaming=True,
        )

        for processed_attachment in processed_attachments_list:
            # Add context information to the attachment data
            attachment_with_context = deepcopy(processed_attachment["attachment"])
            attachment_with_context["_context"] = processed_attachment["context"]

            # Validate and convert to AttachmentProcessingInfo
            validated = self._validate_attachment(attachment_with_context)
            if validated:
                validated_attachments.append(validated)

        return validated_attachments

    def _collect_and_validate_attachments_from_dsr_builder(
        self, data: dict, dsr_builder: "DSRReportBuilder"
    ) -> list[AttachmentProcessingInfo]:
        """Collect and validate attachments using the DSR report builder's processed attachments.

        This method reuses the DSR report builder's processed attachments to avoid
        duplicate processing and ensure consistency.

        Args:
            data: The data dictionary containing items with attachments
            dsr_builder: The DSR report builder instance that has already processed attachments

        Returns:
            List of validated AttachmentProcessingInfo objects
        """
        # Use the DSR report builder's processed attachments
        # Create temporary sets for compatibility with the shared function
        used_filenames_data = set()
        used_filenames_attachments = set()

        # Populate the temporary sets from the DSR builder's per-dataset tracking
        for dataset_name, filenames in dsr_builder.used_filenames_per_dataset.items():
            if dataset_name == "attachments":
                used_filenames_attachments.update(filenames)
            else:
                used_filenames_data.update(filenames)

        return self._collect_and_validate_attachments(
            data,
            used_filenames_data,
            used_filenames_attachments,
            dsr_builder.processed_attachments,
        )

    @retry_cloud_storage_operation(
        provider="smart_open_streaming",
        operation_name="upload_to_storage_streaming",
        max_retries=2,
        base_delay=2.0,
        max_delay=30.0,
    )
    def upload_to_storage_streaming(
        self,
        data: dict,
        config: StorageUploadConfig,
        privacy_request: Optional[PrivacyRequest],
        document: Optional[Any] = None,
        buffer_config: Optional[StreamingBufferConfig] = None,
        batch_size: int = 10,
    ) -> Optional[AnyHttpUrlString]:
        """Upload data to cloud storage using smart-open streaming for memory efficiency.

        This function leverages smart-open's streaming capabilities while maintaining
        our DSR-specific business logic for package and attachment processing.
        All data is streamed directly from source to destination without local storage.

        Args:
            data: Data to upload
            config: Upload configuration
            privacy_request: Privacy request object
            document: Optional document (not yet implemented)
            buffer_config: Buffer configuration
            batch_size: Number of attachments to process in each batch

        Returns:
            presigned_url or None if URL generation fails

        Raises:
            ValueError: If privacy_request is not provided
            NotImplementedError: If document-only upload is attempted
            StorageUploadError: If upload fails
        """
        self._validate_upload_inputs(privacy_request, document)
        if not privacy_request:
            raise ValueError("Privacy request must be provided")

        # Reset used filenames for this upload operation
        self.used_filenames_per_dataset.clear()

        # Use default buffer config if none provided
        if buffer_config is None:
            buffer_config = StreamingBufferConfig()

        try:
            if config.resp_format in [
                ResponseFormat.csv.value,
                ResponseFormat.json.value,
            ]:
                return self._handle_data_format_upload(
                    config, data, privacy_request, buffer_config, batch_size
                )
            if config.resp_format == ResponseFormat.html.value:
                return self._handle_html_format_upload(
                    config, data, privacy_request, buffer_config, batch_size
                )
            raise ValueError(f"Unsupported response format: {config.resp_format}")

        except (ValueError, NotImplementedError):
            # Re-raise validation errors as-is - these are user errors, not system errors
            raise
        except StorageUploadError:
            # Re-raise storage errors as-is
            raise
        except Exception as e:
            # Log unexpected errors and wrap them in StorageUploadError
            logger.error(f"Unexpected error during storage upload: {e}", exc_info=True)
            raise StorageUploadError(
                f"Storage upload failed due to unexpected error: {e}"
            ) from e

    def _validate_upload_inputs(
        self, privacy_request: Optional[PrivacyRequest], document: Optional[Any]
    ) -> None:
        """Validate upload input parameters.

        Args:
            privacy_request: Privacy request object
            document: Optional document

        Raises:
            ValueError: If privacy_request is not provided
            NotImplementedError: If document-only upload is attempted
        """
        if not privacy_request:
            raise ValueError("Privacy request must be provided")

        if document:
            raise NotImplementedError("Document-only uploads not yet implemented")

    def _handle_data_format_upload(
        self,
        config: StorageUploadConfig,
        data: dict,
        privacy_request: PrivacyRequest,
        buffer_config: StreamingBufferConfig,
        batch_size: int,
    ) -> Optional[AnyHttpUrlString]:
        """Handle CSV/JSON format uploads.

        Args:
            config: Upload configuration
            data: Data to upload
            privacy_request: Privacy request object
            buffer_config: Buffer configuration
            batch_size: Number of attachments to process in each batch

        Returns:
            presigned_url or None if URL generation fails
        """
        self._stream_attachments_to_storage_zip(
            config.bucket_name,
            config.file_key,
            data,
            privacy_request,
            config.max_workers,
            buffer_config,
            batch_size,
            config.resp_format,
        )

        # Generate presigned URL for the uploaded file
        try:
            return self.storage_client.generate_presigned_url(
                config.bucket_name, config.file_key
            )
        except Exception as e:
            logger.error(
                f"Failed to generate presigned URL for {config.bucket_name}/{config.file_key}: {e}"
            )
            raise StorageUploadError(f"Failed to generate presigned URL: {e}") from e

    def _handle_html_format_upload(
        self,
        config: StorageUploadConfig,
        data: dict,
        privacy_request: PrivacyRequest,
        buffer_config: StreamingBufferConfig,
        batch_size: int,
    ) -> Optional[AnyHttpUrlString]:
        """Handle HTML format uploads with DSR report generation.

        Args:
            config: Upload configuration
            data: Data to upload
            privacy_request: Privacy request object
            buffer_config: Buffer configuration
            batch_size: Number of attachments to process in each batch

        Returns:
            presigned_url or None if URL generation fails
        """
        # Generate the DSR report first
        try:
            dsr_builder = DSRReportBuilder(
                privacy_request=privacy_request,
                dsr_data=data,
                enable_streaming=True,
            )
            dsr_buffer = dsr_builder.generate()
            # Reset buffer position to ensure it can be read multiple times
            dsr_buffer.seek(0)
        except Exception as e:
            logger.error(f"Failed to generate DSR report: {e}")
            raise StorageUploadError(f"Failed to generate DSR report: {e}") from e

        # Use the DSR report builder's processed attachments to avoid duplicates
        # Use the redacted data from the DSR report builder instead of the original data
        all_attachments = self._collect_and_validate_attachments_from_dsr_builder(
            dsr_builder.dsr_data, dsr_builder
        )

        if not all_attachments:
            # No attachments, just upload the DSR report
            stream_dsr_buffer_to_storage(
                self.storage_client,
                config.bucket_name,
                config.file_key,
                dsr_buffer,
            )

            try:
                return self.storage_client.generate_presigned_url(
                    config.bucket_name, config.file_key
                )
            except Exception as e:
                logger.error(
                    f"Failed to generate presigned URL for {config.file_key}: {e}"
                )
                raise StorageUploadError(
                    f"Failed to generate presigned URL: {e}"
                ) from e
        logger.debug(
            f"Creating HTML DSR report ZIP with {len(all_attachments)} attachments"
        )

        # Create ZIP generator with DSR report files
        dsr_files_generator = create_dsr_report_files_generator(
            dsr_buffer,
            all_attachments,
            config.bucket_name,
            config.max_workers,
            batch_size,
        )

        # Create ZIP generator with attachment files
        attachment_files_generator = self._create_attachment_files(
            all_attachments, buffer_config
        )

        # Combine both generators and stream the complete ZIP to storage
        combined_entries = chain(attachment_files_generator, dsr_files_generator)
        with self.storage_client.stream_upload(
            config.bucket_name,
            config.file_key,
        ) as upload_stream:
            for chunk in stream_zip(combined_entries):
                upload_stream.write(chunk)

        logger.debug(
            f"Successfully uploaded HTML DSR report ZIP with attachments: {config.file_key}"
        )

        # Generate presigned URL for the uploaded file
        try:
            return self.storage_client.generate_presigned_url(
                config.bucket_name, config.file_key
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {config.file_key}: {e}")
            raise StorageUploadError(f"Failed to generate presigned URL: {e}") from e

    @retry_cloud_storage_operation(
        provider="smart_open_streaming",
        operation_name="stream_attachments_to_storage_zip",
        max_retries=2,
        base_delay=2.0,
        max_delay=30.0,
    )
    def _stream_attachments_to_storage_zip(
        self,
        bucket_name: str,
        file_key: str,
        data: dict,
        privacy_request: PrivacyRequest,
        max_workers: int,
        buffer_config: StreamingBufferConfig,
        batch_size: int,
        resp_format: str,
    ) -> None:
        """Stream attachments to storage as a ZIP file using smart-open.

        This method leverages smart-open's streaming capabilities for efficient memory usage.
        Data flows directly from source storage through ZIP generation to destination storage
        without materializing entire files in memory.

        Args:
            bucket_name: Storage bucket name
            file_key: File key in storage
            data: Data to upload
            privacy_request: Privacy request object
            max_workers: Maximum parallel workers
            buffer_config: Buffer configuration
            batch_size: Number of attachments to process in each batch
            resp_format: Response format (csv, json)
        """
        # Collect and validate all attachments using shared contextual processing
        all_attachments = self._collect_and_validate_attachments(
            data=data,
            used_filenames_data=set(),
            used_filenames_attachments=set(),
            processed_attachments={},
        )

        if not all_attachments:
            # No attachments, just upload the data
            self._upload_data_only_zip(bucket_name, file_key, data, resp_format)
            return

        logger.debug(
            f"Starting streaming ZIP creation with {len(all_attachments)} attachments in batches of {batch_size}"
        )

        # Create the ZIP file with data and attachments using smart-open streaming
        zip_generator = self._create_zip_generator(
            data,
            all_attachments,
            bucket_name,
            max_workers,
            batch_size,
            resp_format,
            buffer_config,
        )

        # Use smart-open's streaming upload capability
        with self.storage_client.stream_upload(bucket_name, file_key) as upload_stream:
            for chunk in stream_zip(zip_generator):
                upload_stream.write(chunk)

        logger.debug(
            f"Successfully created memory-efficient streaming ZIP using smart-open: {file_key}"
        )

    def _upload_data_only_zip(
        self, bucket_name: str, file_key: str, data: dict, resp_format: str
    ) -> None:
        """Upload data-only ZIP file (no attachments) using smart-open.

        Args:
            bucket_name: Storage bucket name
            file_key: File key in storage
            data: Data to upload
            resp_format: Response format
        """
        logger.debug("Creating data-only ZIP file (no attachments)")

        # Create data files generator
        data_files_generator = self._create_data_files(data, resp_format)

        # Convert to stream_zip format
        zip_generator = self._convert_to_stream_zip_format(data_files_generator)

        # Use smart-open streaming upload
        with self.storage_client.stream_upload(bucket_name, file_key) as upload_stream:
            for chunk in stream_zip(zip_generator):
                upload_stream.write(chunk)

        logger.debug(f"Successfully uploaded data-only ZIP: {file_key}")

    def _create_zip_generator(
        self,
        data: dict,
        all_attachments: list[AttachmentProcessingInfo],
        bucket_name: str,
        max_workers: int,
        batch_size: int,
        resp_format: str,
        buffer_config: Optional[StreamingBufferConfig] = None,
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Create a generator for ZIP file contents including data and attachments.

        Args:
            data: Data to include in the ZIP
            all_attachments: List of validated attachments
            bucket_name: Storage bucket name
            max_workers: Maximum parallel workers
            batch_size: Number of attachments to process in each batch
            resp_format: Response format

        Returns:
            Generator yielding ZIP file entries in stream_zip format
        """
        logger.debug(f"Creating ZIP generator with {len(all_attachments)} attachments")

        # For HTML format, data files are not needed as the DSR report contains the HTML content
        if resp_format.lower() != "html":
            # First, yield data files (convert to stream_zip format and stream directly)
            data_files_generator = self._create_data_files(
                data, resp_format, all_attachments
            )
            yield from self._convert_to_stream_zip_format(data_files_generator)

        # Then, yield attachment files (already in stream_zip format, stream directly)
        attachment_files_generator = self._create_attachment_files(
            all_attachments, buffer_config
        )
        yield from attachment_files_generator

    def _create_data_files(
        self,
        data: dict,
        resp_format: str = "json",
        all_attachments: Optional[list[AttachmentProcessingInfo]] = None,
    ) -> Generator[Tuple[str, BytesIO, dict[str, Any]], None, None]:
        """Create data files (JSON/CSV) from the input data based on resp_format configuration."""

        # Transform data to use internal access package URLs if attachments are provided
        if all_attachments:
            data = self._transform_data_for_access_package(data, all_attachments)

        for key, value in data.items():
            if isinstance(value, list) and value:
                # Use the configured response format instead of making decisions based on content
                if resp_format.lower() == "json":
                    data_content = json.dumps(value, default=str).encode("utf-8")
                    yield f"{key}.json", BytesIO(data_content), {}
                elif resp_format.lower() == "csv":
                    csv_buffer = StringIO()
                    if value and isinstance(value[0], dict):
                        writer = csv.DictWriter(csv_buffer, fieldnames=value[0].keys())
                        writer.writeheader()
                        writer.writerows(value)
                        data_content = csv_buffer.getvalue().encode("utf-8")
                        yield f"{key}.csv", BytesIO(data_content), {}
                    else:
                        # Fallback to JSON for non-dict list items when CSV is requested
                        data_content = json.dumps(value, default=str).encode("utf-8")
                        yield f"{key}.json", BytesIO(data_content), {}
                elif resp_format.lower() == "html":
                    # HTML format typically uses JSON for data files since HTML is for the report itself
                    data_content = json.dumps(value, default=str).encode("utf-8")
                    yield f"{key}.json", BytesIO(data_content), {}
                else:
                    # Default to JSON for unsupported formats
                    data_content = json.dumps(value, default=str).encode("utf-8")
                    yield f"{key}.json", BytesIO(data_content), {}

    def _handle_attachment_error(
        self,
        all_attachments: list[AttachmentProcessingInfo],
        failed_attachments: list[dict[str, Optional[str]]],
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Handle attachment errors and create a summary file."""

        try:
            # Calculate success rate with division by zero protection
            total_attempted = len(all_attachments)
            total_failed = len(failed_attachments)
            success_rate = "N/A"

            if total_attempted > 0:
                success_rate = (
                    f"{((total_attempted - total_failed) / total_attempted * 100):.1f}%"
                )

            error_summary = {
                "failed_attachments": failed_attachments,
                "total_failed": total_failed,
                "total_attempted": total_attempted,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat(),
            }

            error_summary_content = json.dumps(error_summary, indent=2).encode("utf-8")
            yield (
                "errors/attachment_failures_summary.json",
                datetime.now(),
                DEFAULT_FILE_MODE,
                _ZIP_32_TYPE(),
                iter([error_summary_content]),
            )
        except Exception as summary_error:
            logger.error(f"Failed to create error summary: {summary_error}")
            # Create a minimal error summary as fallback
            fallback_summary = {
                "error": "Failed to generate detailed error summary",
                "total_failed": len(failed_attachments),
                "total_attempted": len(all_attachments),
                "timestamp": datetime.now().isoformat(),
            }
            fallback_content = json.dumps(fallback_summary, indent=2).encode("utf-8")
            yield (
                "errors/attachment_failures_summary.json",
                datetime.now(),
                DEFAULT_FILE_MODE,
                _ZIP_32_TYPE(),
                iter([fallback_content]),
            )

    def _create_attachment_files(
        self,
        all_attachments: list[AttachmentProcessingInfo],
        buffer_config: Optional[StreamingBufferConfig] = None,
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Create attachment files for the ZIP using true cloud-to-cloud streaming.

        This method yields stream_zip format entries without loading entire files to memory.
        Each attachment is processed as a streaming iterator that yields chunks directly
        from source storage to ZIP generation.

        Args:
            all_attachments: List of validated attachments
            buffer_config: Configuration for error handling behavior

        Returns:
            Generator yielding attachment file entries in stream_zip format
        """
        if buffer_config is None:
            buffer_config = StreamingBufferConfig()

        failed_attachments = []

        for attachment_info in all_attachments:
            try:
                result = self._process_attachment_safely(attachment_info)
                yield result
            except StorageUploadError as e:
                # Log the failure
                failed_attachments.append(
                    {
                        "attachment": attachment_info.attachment.file_name,
                        "storage_key": attachment_info.attachment.storage_key,
                        "error": str(e),
                    }
                )
                logger.error(
                    f"Failed to process attachment {attachment_info.attachment.file_name} "
                    f"({attachment_info.attachment.storage_key}): {e}"
                )

                # If fail_fast is enabled, re-raise the exception
                if buffer_config.fail_fast_on_attachment_errors:
                    raise

                # Create a placeholder file with error information if error details are enabled
                if buffer_config.include_error_details:
                    error_content = (
                        f"Error: Failed to retrieve attachment - {e}".encode("utf-8")
                    )
                    error_filename = (
                        f"ERROR_{attachment_info.attachment.file_name or 'unknown'}"
                    )
                    yield (
                        f"errors/{error_filename}",
                        datetime.now(),
                        DEFAULT_FILE_MODE,
                        _ZIP_32_TYPE(),
                        iter([error_content]),
                    )

        # Log summary of failed attachments
        if failed_attachments:
            logger.warning(
                f"Failed to process {len(failed_attachments)} attachments: "
                f"{[att['attachment'] for att in failed_attachments]}"
            )

            # Create a summary error file with details about all failures if error details are enabled
            if buffer_config.include_error_details:
                yield from self._handle_attachment_error(
                    all_attachments, failed_attachments
                )

    def _transform_data_for_access_package(
        self, data: dict[str, Any], all_attachments: list[AttachmentProcessingInfo]
    ) -> dict[str, Any]:
        """
        Transform the data structure to replace download URLs with internal access package paths.
        This ensures that when data is serialized to JSON/CSV, it contains internal references
        instead of external download URLs.
        """
        if not all_attachments:
            return data

        # Create a simple mapping of original URLs to internal paths
        url_mapping = {
            attachment.attachment.storage_key: f"attachments/{attachment.attachment.file_name or f'attachment_{id(attachment.attachment)}'}"
            for attachment in all_attachments
            if attachment.attachment.storage_key.startswith(("http://", "https://"))
        }

        if not url_mapping:
            return data

        # Simple recursive replacement
        def replace_urls(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: replace_urls(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [replace_urls(item) for item in obj]
            if isinstance(obj, str) and obj in url_mapping:
                return url_mapping[obj]
            return obj

        return replace_urls(data)

    def _process_attachment_safely(
        self,
        attachment_info: AttachmentProcessingInfo,
    ) -> tuple[str, datetime, int, Any, Iterable[bytes]]:
        """Process attachment with consistent error handling.

        Args:
            attachment_info: Attachment processing information

        Returns:
            Stream ZIP format tuple

        Raises:
            StorageUploadError: If attachment processing fails for any reason
        """
        try:
            storage_key = attachment_info.attachment.storage_key

            try:
                source_bucket, source_key = self._parse_storage_url(storage_key)
            except ValueError as e:
                raise StorageUploadError(
                    f"Could not parse storage URL: {storage_key} - {e}"
                ) from e

            # Generate unique filename using same logic as DSR report builder
            original_filename = (
                attachment_info.attachment.file_name or DEFAULT_ATTACHMENT_NAME
            )

            # Determine dataset name from base_path using shared utility
            dataset_name = determine_dataset_name_from_path(attachment_info.base_path)

            if dataset_name not in self.used_filenames_per_dataset:
                self.used_filenames_per_dataset[dataset_name] = set()

            unique_filename = get_unique_filename(
                original_filename, self.used_filenames_per_dataset[dataset_name]
            )
            self.used_filenames_per_dataset[dataset_name].add(unique_filename)
            file_path = resolve_attachment_storage_path(
                unique_filename, attachment_info.base_path
            )

            try:
                content_stream = self._create_attachment_content_stream(
                    source_bucket, source_key, storage_key
                )
                return (
                    file_path,
                    datetime.now(),
                    DEFAULT_FILE_MODE,
                    _ZIP_32_TYPE(),
                    content_stream,
                )
            except Exception as e:
                logger.error(
                    f"Failed to create content stream for attachment {storage_key}: {e}"
                )
                raise StorageUploadError(
                    f"Failed to create content stream for attachment: {e}"
                ) from e

        except Exception as e:
            logger.error(
                f"Failed to process attachment {attachment_info.attachment.storage_key}: {e}",
                exc_info=True,
            )
            raise StorageUploadError(
                f"Failed to process attachment {attachment_info.attachment.storage_key}: {e}"
            ) from e
