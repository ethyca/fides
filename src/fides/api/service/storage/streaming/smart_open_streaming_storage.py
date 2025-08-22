"""Smart-open based streaming storage for efficient cloud-to-cloud data transfer."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Generator, Iterable, Optional, Tuple

from fideslang.validation import AnyHttpUrlString
from loguru import logger
from stream_zip import _ZIP_32_TYPE, stream_zip

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)
from fides.api.service.storage.streaming.dsr_storage import (
    create_dsr_report_files_generator,
    stream_dsr_buffer_to_storage,
)
from fides.api.service.storage.streaming.retry import retry_cloud_storage_operation
from fides.api.service.storage.streaming.schemas import (
    CHUNK_SIZE_THRESHOLD,
    AttachmentInfo,
    AttachmentProcessingInfo,
    PackageSplitConfig,
    StorageUploadConfig,
    StreamingBufferConfig,
)
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


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
        chunk_size: int = CHUNK_SIZE_THRESHOLD,
    ):
        """Initialize with a smart-open storage client.

        Args:
            storage_client: Smart-open based storage client
            chunk_size: Size of chunks for streaming attachments (default: 8KB)
        """
        self.storage_client = storage_client
        self.chunk_size = chunk_size

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

            yield filename, datetime.now(), 0o644, _ZIP_32_TYPE(), iter([content_bytes])

    def build_attachments_list(
        self, data: dict, config: PackageSplitConfig
    ) -> list[tuple[str, dict, int]]:
        """
        Build a list of attachments from the data.

        Args:
            data: The data to build the attachments list from
            config: The configuration for package splitting

        Returns:
            A list of AttachmentInfo objects
        """
        attachments_list = []
        for key, value in data.items():
            if not isinstance(value, list):
                continue

            for item in value:
                attachments = item.get("attachments", [])
                if not isinstance(attachments, list):
                    attachments = []

                attachment_count = len(attachments)

                # Only include items that have attachments
                if attachment_count > 0:
                    # If a single item has more attachments than the limit, we need to split it
                    if attachment_count > config.max_attachments:
                        # Split the item into multiple sub-items
                        for i in range(0, attachment_count, config.max_attachments):
                            sub_attachments = attachments[
                                i : i + config.max_attachments
                            ]
                            sub_item = item.copy()
                            sub_item["attachments"] = sub_attachments
                            attachments_list.append(
                                (key, sub_item, len(sub_attachments))
                            )
                    else:
                        attachments_list.append((key, item, attachment_count))

        return attachments_list

    def split_data_into_packages(
        self, data: dict, config: Optional[PackageSplitConfig] = None
    ) -> list[dict]:
        """Split large datasets into multiple smaller packages.

        Uses a best-fit decreasing algorithm to optimize package distribution:
        1. Sort items by attachment count (largest first)
        2. Try to fit each item in the package with the most remaining space
        3. Create new packages only when necessary
        4. Handle items that exceed the max_attachments limit by splitting them

        Args:
            data: The data to split
            config: Configuration for package splitting (defaults to PackageSplitConfig())

        Returns:
            List of data packages
        """
        # Use default config if none provided
        if config is None:
            config = PackageSplitConfig()

        # Collect all items with their attachment counts
        all_items = self.build_attachments_list(data, config)

        # Sort by attachment count (largest first) for better space utilization
        all_items.sort(key=lambda x: x[2], reverse=True)

        packages: list[dict[str, Any]] = []
        package_attachment_counts: list[int] = []

        for key, item, attachment_count in all_items:
            # Try to find a package with enough space
            package_found = False

            for i, current_count in enumerate(package_attachment_counts):
                if current_count + attachment_count <= config.max_attachments:
                    # Add to existing package
                    if key not in packages[i]:
                        packages[i][key] = []
                    packages[i][key].append(item)
                    package_attachment_counts[i] += attachment_count
                    package_found = True
                    break

            if not package_found:
                # Create new package - this item cannot fit in any existing package
                new_package = {key: [item]}
                packages.append(new_package)
                package_attachment_counts.append(attachment_count)

        return packages

    def _collect_attachments(self, data: dict) -> list[dict]:
        """Collect all attachment data from the input data structure.

        This method handles both direct attachments (under 'attachments' key) and
        nested attachments within items. It returns raw attachment data without validation.

        Args:
            data: The data dictionary containing items with attachments

        Returns:
            List of raw attachment dictionaries with metadata
        """
        all_attachments = []

        for key, value in data.items():
            logger.debug(f"Processing key '{key}' with value type: {type(value)}")

            if not isinstance(value, list) or not value:
                continue

            # Collect direct attachments if this key is "attachments"
            if key == "attachments":
                all_attachments.extend(self._collect_direct_attachments(value))

            # Collect nested attachments from items
            all_attachments.extend(self._collect_nested_attachments(key, value))

        logger.debug(f"Collected {len(all_attachments)} raw attachments")
        return all_attachments

    def _collect_direct_attachments(self, attachments_list: list) -> list[dict]:
        """Collect attachments from a direct attachments list.

        Args:
            attachments_list: List of attachment dictionaries

        Returns:
            List of attachment data dictionaries with metadata
        """
        direct_attachments = []

        logger.debug(
            f"Found 'attachments' key with {len(attachments_list)} items - processing as direct attachments"
        )

        for idx, attachment in enumerate(attachments_list):
            if not isinstance(attachment, dict):
                continue

            # Check if this looks like an attachment (has file_name or download_url)
            if "file_name" in attachment or "download_url" in attachment:
                # Transform download_url to internal access package URL for access package display
                if "download_url" in attachment:
                    attachment["original_download_url"] = attachment["download_url"]
                    attachment["download_url"] = (
                        f"attachments/{attachment.get('file_name', f'attachment_{idx}')}"
                    )

                direct_attachments.append(attachment)

        return direct_attachments

    def _collect_nested_attachments(self, key: str, items: list) -> list[dict]:
        """Collect attachments from nested items.

        Args:
            key: The key for the items list
            items: List of items that may contain attachments

        Returns:
            List of attachment data dictionaries with metadata
        """
        nested_attachments = []

        for item in items:
            if not isinstance(item, dict):
                continue

            # Recursively search for attachments in nested structures
            item_attachments = self._find_attachments_recursive(item, key)
            nested_attachments.extend(item_attachments)

        return nested_attachments

    def _find_attachments_recursive(
        self, item: dict, context_key: str, path: str = ""
    ) -> list[dict]:
        """Recursively find attachments in nested dictionary structures.

        Args:
            item: Dictionary item to search
            context_key: The top-level key for context
            path: Current path in the nested structure

        Returns:
            List of attachment data dictionaries with metadata
        """
        attachments = []

        # Check if this item has direct attachments
        if "attachments" in item and isinstance(item["attachments"], list):
            for attachment in item["attachments"]:
                if not isinstance(attachment, dict):
                    continue

                # Check if this looks like an attachment
                if "file_name" in attachment or "download_url" in attachment:
                    # Add context about which item this attachment belongs to
                    attachment_with_context = attachment.copy()
                    attachment_with_context["_context"] = {
                        "key": context_key,
                        "item_id": item.get("id", "unknown"),
                        "path": path,
                    }

                    # Transform download_url to internal access package URL
                    if "download_url" in attachment:
                        attachment_with_context["original_download_url"] = attachment[
                            "download_url"
                        ]
                        attachment_with_context["download_url"] = (
                            f"attachments/{attachment.get('file_name', 'attachment')}"
                        )

                    attachments.append(attachment_with_context)

        # Recursively search nested dictionaries
        for key, value in item.items():
            if isinstance(value, dict):
                current_path = f"{path}.{key}" if path else key
                nested_attachments = self._find_attachments_recursive(
                    value, context_key, current_path
                )
                attachments.extend(nested_attachments)

        return attachments

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
            # Extract required fields - use original_download_url for storage operations
            storage_key = (
                attachment.get("original_download_url")
                or attachment.get("download_url")
                or attachment.get("file_name", "")
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

            # Create base path for the attachment in the zip
            base_path = "attachments"
            if attachment.get("_context"):
                context = attachment["_context"]
                base_path = f"{context['key']}/{context['item_id']}/attachments"

            # Create AttachmentProcessingInfo
            processing_info = AttachmentProcessingInfo(
                attachment=attachment_info,
                base_path=base_path,
                item=attachment,
            )

            logger.debug(
                f"Successfully validated attachment: {attachment_info.storage_key}"
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
        try:
            logger.debug(
                f"Starting streaming read of {storage_key} from bucket: {bucket}, key: {key}"
            )
            with self.storage_client.stream_read(bucket, key) as content_stream:
                # Stream in chunks instead of reading entire file
                chunk_count = 0
                total_bytes = 0
                while True:
                    chunk = content_stream.read(self.chunk_size)
                    if not chunk:
                        break
                    chunk_count += 1
                    total_bytes += len(chunk)
                    yield chunk

                logger.debug(
                    f"Completed streaming {chunk_count} chunks ({total_bytes} bytes) for {storage_key}"
                )
        except Exception as e:
            logger.warning(f"Failed to stream attachment {storage_key}: {e}")
            # Yield empty content on failure
            yield b""

    def _collect_and_validate_attachments(
        self, data: dict
    ) -> list[AttachmentProcessingInfo]:
        """Collect and validate all attachments from the data.

        This method now delegates to _collect_attachments and _validate_attachment
        for better separation of concerns and readability.

        Args:
            data: The data dictionary containing items with attachments

        Returns:
            List of validated AttachmentProcessingInfo objects
        """
        # Collect raw attachment data
        raw_attachments = self._collect_attachments(data)

        # Validate and convert each attachment
        validated_attachments = []
        for attachment_data in raw_attachments:
            validated = self._validate_attachment(attachment_data)
            if validated:
                validated_attachments.append(validated)

        logger.debug(
            f"Successfully validated {len(validated_attachments)} out of {len(raw_attachments)} attachments"
        )
        return validated_attachments

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
        our DSR-specific business logic for package splitting and attachment processing.
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
        if not privacy_request:
            raise ValueError("Privacy request must be provided")

        if document:
            raise NotImplementedError("Document-only uploads not yet implemented")

        # Use default buffer config if none provided
        if buffer_config is None:
            buffer_config = StreamingBufferConfig()

        try:
            if config.resp_format == ResponseFormat.csv.value:
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

            elif config.resp_format == ResponseFormat.json.value:
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

            elif config.resp_format == ResponseFormat.html.value:
                # For HTML, we need to handle the DSR report generation AND attachments
                # Generate the DSR report first, then create a ZIP with both report and attachments
                dsr_buffer = DsrReportBuilder(
                    privacy_request=privacy_request,
                    dsr_data=data,
                ).generate()

                # Check if there are attachments to include
                all_attachments = self._collect_and_validate_attachments(data)

                if not all_attachments:
                    # No attachments, just upload the DSR report
                    stream_dsr_buffer_to_storage(
                        self.storage_client,
                        config.bucket_name,
                        config.file_key,
                        dsr_buffer,
                    )
                else:
                    # Create a ZIP containing both the DSR report and attachments
                    logger.info(
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
                        all_attachments,
                        config.bucket_name,
                        config.max_workers,
                        batch_size,
                    )

                    # Combine both generators and stream the complete ZIP to storage
                    with self.storage_client.stream_upload(
                        config.bucket_name,
                        config.file_key,
                        content_type="application/zip",
                    ) as upload_stream:
                        # First stream the DSR report files
                        for chunk in stream_zip(dsr_files_generator):
                            upload_stream.write(chunk)

                        # Then stream the attachment files
                        for chunk in stream_zip(attachment_files_generator):
                            upload_stream.write(chunk)

                    logger.info(
                        f"Successfully uploaded HTML DSR report ZIP with attachments: {config.file_key}"
                    )

            else:
                raise ValueError(f"Unsupported response format: {config.resp_format}")

            # Generate presigned URL for the uploaded file
            return self.storage_client.generate_presigned_url(
                config.bucket_name, config.file_key
            )

        except Exception as e:
            logger.error(f"Failed to upload data to storage: {e}")
            raise StorageUploadError(f"Storage upload failed: {e}") from e

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
        # Collect and validate all attachments
        all_attachments = self._collect_and_validate_attachments(data)

        if not all_attachments:
            # No attachments, just upload the data
            self._upload_data_only_zip(bucket_name, file_key, data, resp_format)
            return

        logger.info(
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
        )

        # Use smart-open's streaming upload capability
        with self.storage_client.stream_upload(
            bucket_name, file_key, content_type="application/zip"
        ) as upload_stream:
            for chunk in stream_zip(zip_generator):
                upload_stream.write(chunk)

        logger.info(
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
        logger.info("Creating data-only ZIP file (no attachments)")

        # Create data files generator
        data_files_generator = self._create_data_files(data, resp_format)

        # Convert to stream_zip format
        zip_generator = self._convert_to_stream_zip_format(data_files_generator)

        # Use smart-open streaming upload
        with self.storage_client.stream_upload(
            bucket_name, file_key, content_type="application/zip"
        ) as upload_stream:
            for chunk in stream_zip(zip_generator):
                upload_stream.write(chunk)

        logger.info(f"Successfully uploaded data-only ZIP: {file_key}")

    def _create_zip_generator(
        self,
        data: dict,
        all_attachments: list[AttachmentProcessingInfo],
        bucket_name: str,
        max_workers: int,
        batch_size: int,
        resp_format: str,
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
        logger.info(f"Creating ZIP generator with {len(all_attachments)} attachments")

        # First, yield data files (convert to stream_zip format and stream directly)
        data_files_generator = self._create_data_files(
            data, resp_format, all_attachments
        )
        logger.info("Yielding data files for ZIP")
        yield from self._convert_to_stream_zip_format(data_files_generator)

        # Then, yield attachment files (already in stream_zip format, stream directly)
        attachment_files_generator = self._create_attachment_files(
            all_attachments, bucket_name, max_workers, batch_size
        )
        logger.info("Yielding attachment files for ZIP")
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

    def _create_attachment_files(
        self,
        all_attachments: list[AttachmentProcessingInfo],
        bucket_name: str,
        max_workers: int,
        batch_size: int,
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Create attachment files for the ZIP using true cloud-to-cloud streaming.

        This method yields stream_zip format entries without loading entire files to memory.
        Each attachment is processed as a streaming iterator that yields chunks directly
        from source storage to ZIP generation.

        Args:
            all_attachments: List of validated attachments
            bucket_name: Storage bucket name
            max_workers: Maximum parallel workers
            batch_size: Number of attachments to process in each batch

        Returns:
            Generator yielding attachment file entries in stream_zip format
        """
        logger.info(f"Processing {len(all_attachments)} attachments for ZIP creation")

        for attachment_info in all_attachments:
            try:
                logger.debug(
                    f"Processing attachment: {attachment_info.attachment.file_name} with storage_key: {attachment_info.attachment.storage_key}"
                )

                # Extract bucket and key from storage key
                storage_key = attachment_info.attachment.storage_key
                source_bucket = bucket_name
                source_key = storage_key

                if storage_key.startswith("s3://"):
                    # Extract bucket from S3 URL: s3://bucket/path
                    bucket_from_key = storage_key.split("/")[2]
                    source_bucket = bucket_from_key
                    source_key = "/".join(storage_key.split("/")[3:])
                    logger.debug(
                        f"Parsed S3 URL - bucket: {source_bucket}, key: {source_key}"
                    )
                elif (
                    storage_key.startswith("https://")
                    and ".s3.amazonaws.com" in storage_key
                ):
                    # Extract bucket and key from HTTP S3 URL: https://bucket.s3.amazonaws.com/key
                    # Remove query parameters first
                    clean_url = storage_key.split("?")[0]
                    # Split by .s3.amazonaws.com and extract bucket and key
                    parts = clean_url.split(".s3.amazonaws.com/")
                    if len(parts) == 2:
                        bucket_part = parts[0].replace("https://", "")
                        source_bucket = bucket_part
                        source_key = parts[1]
                        logger.debug(
                            f"Parsed HTTPS S3 URL - bucket: {source_bucket}, key: {source_key}"
                        )
                    else:
                        logger.warning(f"Could not parse S3 HTTP URL: {storage_key}")
                        continue
                elif (
                    storage_key.startswith("http://")
                    and ".s3.amazonaws.com" in storage_key
                ):
                    # Handle HTTP (non-HTTPS) S3 URLs
                    clean_url = storage_key.split("?")[0]
                    parts = clean_url.split(".s3.amazonaws.com/")
                    if len(parts) == 2:
                        bucket_part = parts[0].replace("http://", "")
                        source_bucket = bucket_part
                        source_key = parts[1]
                        logger.debug(
                            f"Parsed HTTP S3 URL - bucket: {source_bucket}, key: {source_key}"
                        )
                    else:
                        logger.warning(f"Could not parse S3 HTTP URL: {storage_key}")
                        continue

                # Create the file path in the ZIP
                file_path = f"{attachment_info.base_path}/{attachment_info.attachment.file_name or 'attachment'}"
                logger.debug(f"Adding attachment to ZIP at path: {file_path}")

                # Yield in stream_zip format: (filename, datetime, mode, method, content_iter)
                yield file_path, datetime.now(), 0o644, _ZIP_32_TYPE(), self._create_attachment_content_stream(
                    source_bucket, source_key, storage_key
                )

            except Exception as e:
                logger.warning(
                    f"Failed to process attachment {attachment_info.attachment.storage_key}: {e}"
                )
                # Continue with other attachments
                continue

    def _transform_data_for_access_package(
        self, data: dict, all_attachments: list[AttachmentProcessingInfo]
    ) -> dict:
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
