from __future__ import annotations

import csv
import json
from datetime import datetime
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Generator, Iterable, Optional, Tuple

import requests
from fideslang.validation import AnyHttpUrlString
from loguru import logger
from stream_zip import _ZIP_32_TYPE, stream_zip

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.dsr_storage import (
    stream_html_dsr_report_to_storage_multipart,
)
from fides.api.service.storage.streaming.retry import retry_cloud_storage_operation
from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    AttachmentProcessingInfo,
    PackageSplitConfig,
    StorageUploadConfig,
    StreamingBufferConfig,
)

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


class StreamingStorage:
    def __init__(self, storage_client: CloudStorageClient):
        self.storage_client = storage_client

    def _convert_to_stream_zip_format(
        self, generator: Generator[Tuple[str, BytesIO, dict[str, Any]], None, None]
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Convert generator from (filename, BytesIO, metadata) to (filename, datetime, mode, method, content_iter) format.

        This adapter converts our internal generator format to the format expected by stream_zip.
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
                # Keep original URL for actual file access
                original_url = attachment.get("download_url") or attachment.get("url")
                file_name = attachment.get("file_name", f"attachment_{idx}")
                internal_access_url = f"attachments/{file_name}"

                # Create a copy of the attachment with transformed URLs for access package
                transformed_attachment = attachment.copy()
                transformed_attachment["url"] = internal_access_url
                transformed_attachment["download_url"] = internal_access_url
                transformed_attachment["storage_key"] = (
                    original_url  # Keep original for file access
                )

                # Add metadata for processing
                attachment_data = {
                    "attachment": transformed_attachment,
                    "base_path": f"attachments/{idx + 1}",
                    "item": attachment,
                    "type": "direct",
                }
                direct_attachments.append(attachment_data)
                logger.debug(
                    f"Added direct attachment: {attachment.get('file_name', f'attachment_{idx}')}"
                )

        return direct_attachments

    def _collect_nested_attachments(self, key: str, items: list) -> list[dict]:
        """Collect nested attachments from items in a list.

        Args:
            key: The key name for the items list
            items: List of items that may contain attachments

        Returns:
            List of attachment data dictionaries with metadata
        """
        nested_attachments = []

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            # Check for standard attachments list
            nested_attachments.extend(
                self._collect_standard_nested_attachments(key, idx, item)
            )

            # Check for task-based attachment structure
            nested_attachments.extend(
                self._collect_task_based_attachments(key, idx, item)
            )

        return nested_attachments

    def _collect_standard_nested_attachments(
        self, key: str, idx: int, item: dict
    ) -> list[dict]:
        """Collect standard nested attachments from an item's attachments list.

        Args:
            key: The key name for the items list
            idx: Index of the item in the list
            item: The item dictionary

        Returns:
            List of attachment data dictionaries with metadata
        """
        attachments = item.get("attachments", [])
        if not isinstance(attachments, list):
            return []

        standard_attachments = []
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue

            # Add metadata for processing
            attachment_data = {
                "attachment": attachment,
                "base_path": f"{key}/{idx + 1}/attachments",
                "item": item,
                "type": "nested",
            }
            standard_attachments.append(attachment_data)

        return standard_attachments

    def _collect_task_based_attachments(
        self, key: str, idx: int, item: dict
    ) -> list[dict]:
        """Collect task-based attachments from an item's task keys.

        Args:
            key: The key name for the items list
            idx: Index of the item in the list
            item: The item dictionary

        Returns:
            List of attachment data dictionaries with metadata
        """
        task_attachments = []

        # Look for keys that might contain attachment data (e.g., "access_task", "erasure_task", etc.)
        for task_key, task_value in item.items():
            if not isinstance(task_value, dict):
                continue

            # Check if this looks like a task with file attachments
            # Files are keys with values containing url/size (like your data structure)
            for filename, file_data in task_value.items():
                if not isinstance(file_data, dict):
                    continue

                # Check if this looks like an attachment (has url, size, etc.)
                if "url" in file_data or "download_url" in file_data:
                    # Transform download_url to internal access package URL
                    # This URL should point to where the attachment is located within the access package
                    original_url = file_data.get("url") or file_data.get("download_url")
                    internal_access_url = f"attachments/{filename}"

                    # Create attachment object with filename and file data
                    attachment_obj = {
                        "file_name": filename,
                        "url": internal_access_url,  # Use internal access package URL
                        "download_url": internal_access_url,  # Use internal access package URL
                        "file_size": file_data.get("size"),
                        "content_type": file_data.get("content_type"),
                        "storage_key": original_url,  # Keep original URL for actual file access
                    }

                    attachment_data = {
                        "attachment": attachment_obj,
                        "base_path": f"{key}/{idx + 1}/{task_key}",
                        "item": item,
                        "type": "nested",
                    }
                    task_attachments.append(attachment_data)
                    logger.debug(
                        f"Added task-based attachment: {filename} from {task_key}"
                    )

        return task_attachments

    def _validate_attachment(
        self, attachment_data: dict
    ) -> Optional[AttachmentProcessingInfo]:
        """Validate a single attachment and convert it to AttachmentProcessingInfo.

        Args:
            attachment_data: Dictionary containing attachment data and metadata

        Returns:
            Validated AttachmentProcessingInfo or None if validation fails
        """
        attachment = attachment_data["attachment"]
        base_path = attachment_data["base_path"]
        item = attachment_data["item"]
        attachment_type = attachment_data["type"]

        # Validate that attachment is a dictionary
        if not isinstance(attachment, dict):
            logger.debug(f"Skipping attachment with invalid type: {type(attachment)}")
            return None

        try:
            if attachment_type == "direct":
                # Handle direct attachments (from 'attachments' key)
                # Use storage_key if available (contains original URL for file access)
                # Otherwise fall back to download_url or url
                storage_key = attachment.get("storage_key") or attachment.get(
                    "download_url",
                    attachment.get("url", f"attachment_{id(attachment)}"),
                )
                file_name = attachment.get("file_name", f"attachment_{id(attachment)}")

                attachment_info = AttachmentInfo(
                    storage_key=storage_key,
                    file_name=file_name,
                    size=attachment.get("file_size"),
                    content_type=attachment.get("content_type"),
                )
            else:
                # Handle nested attachments (require storage_key)
                if "storage_key" not in attachment:
                    logger.debug(
                        f"Skipping attachment without storage_key: {attachment}"
                    )
                    return None

                attachment_info = AttachmentInfo(**attachment)

            processing_info = AttachmentProcessingInfo(
                attachment=attachment_info,
                base_path=base_path,
                item=item,
            )

            logger.debug(
                f"Successfully validated attachment: {attachment_info.storage_key}"
            )
            return processing_info

        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Failed to validate attachment: {attachment}, error: {e}")
            return None

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
        provider="cloud storage",
        operation_name="upload to storage streaming",
        max_retries=2,
        base_delay=2.0,
        max_delay=30.0,
    )
    def upload_to_storage_streaming(
        self,
        storage_client: CloudStorageClient,
        data: dict,
        config: StorageUploadConfig,
        privacy_request: Optional[PrivacyRequest],
        document: Optional[Any] = None,
        buffer_config: Optional[StreamingBufferConfig] = None,
        batch_size: int = 10,
    ) -> Optional[AnyHttpUrlString]:
        """Upload data to cloud storage using streaming for memory efficiency.

        This function implements true streaming from source to destination cloud storage,
        minimizing local memory usage by processing attachments in controlled batches.

        Args:
            storage_client: Cloud storage client
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
                self.stream_attachments_to_storage_zip(
                    storage_client,
                    config.bucket_name,
                    config.file_key,
                    data,
                    privacy_request,
                    config.max_workers,
                    buffer_config,
                    batch_size,
                )

            elif config.resp_format == ResponseFormat.json.value:
                self.stream_attachments_to_storage_zip(
                    storage_client,
                    config.bucket_name,
                    config.file_key,
                    data,
                    privacy_request,
                    config.max_workers,
                    buffer_config,
                    batch_size,
                )

            elif config.resp_format == ResponseFormat.html.value:
                # HTML format uses different streaming approach
                stream_html_dsr_report_to_storage_multipart(
                    storage_client,
                    config.bucket_name,
                    config.file_key,
                    data,
                    privacy_request,
                )

            else:
                raise StorageUploadError(
                    f"Unexpected error during true streaming upload: unsupported format {config.resp_format}"
                )

            # Generate presigned URL for download
            try:
                presigned_url = storage_client.generate_presigned_url(
                    config.bucket_name, config.file_key
                )
            except (ValueError, AttributeError) as e:
                # Handle configuration or method availability issues
                logger.warning(
                    "Failed to generate presigned URL for {}: {}", config.file_key, e
                )
                presigned_url = None
            except Exception as e:
                # Catch any other unexpected errors during presigned URL generation
                logger.warning(
                    "Unexpected error generating presigned URL for {}: {}",
                    config.file_key,
                    e,
                )
                presigned_url = None

            return presigned_url

        except (ValueError, AttributeError) as e:
            # Handle configuration or validation errors
            error_msg = f"Configuration error during true streaming upload: {e}"
            logger.error(error_msg)
            raise StorageUploadError(error_msg) from e
        except Exception as e:
            # Catch any other unexpected errors
            error_msg = f"Unexpected error during true streaming upload: {e}"
            logger.error(error_msg)
            raise StorageUploadError(error_msg) from e

    @retry_cloud_storage_operation(
        provider="cloud storage",
        operation_name="stream attachments to storage ZIP (memory efficient)",
        max_retries=2,
        base_delay=2.0,
        max_delay=30.0,
    )
    def stream_attachments_to_storage_zip(
        self,
        storage_client: CloudStorageClient,
        bucket_name: str,
        file_key: str,
        data: dict,
        privacy_request: PrivacyRequest,
        max_workers: int = 5,
        buffer_config: Optional[StreamingBufferConfig] = None,
        batch_size: int = 10,
        resp_format: str = "json",
    ) -> None:
        """Stream attachments with minimal memory usage using controlled concurrency and batch processing.

        This function processes attachments in small batches with controlled concurrency within each batch
        to keep memory usage low and predictable, even for very large datasets.

        Args:
            storage_client: Cloud storage client
            bucket_name: Bucket name for upload
            file_key: File key for the ZIP file
            data: Data containing attachments
            privacy_request: Privacy request object
            max_workers: Maximum number of parallel workers for downloads
            buffer_config: Buffer configuration
            batch_size: Number of attachments to process in each batch
        """
        if buffer_config is None:
            buffer_config = StreamingBufferConfig()

        all_attachments = self._collect_and_validate_attachments(data)

        if not all_attachments:
            logger.info("No attachments found, creating data-only ZIP")
            self._upload_data_only_zip(
                storage_client, bucket_name, file_key, data, resp_format
            )
            return

        logger.info(
            f"Starting streaming ZIP creation with {len(all_attachments)} attachments in batches of {batch_size}"
        )

        # Create the ZIP file with data and attachments
        zip_generator = self._create_zip_generator(
            data,
            all_attachments,
            storage_client,
            bucket_name,
            max_workers,
            batch_size,
            resp_format,
        )

        # The generator is already in stream_zip format, so use it directly
        storage_client.put_object(
            bucket_name,
            file_key,
            stream_zip(zip_generator),
            content_type="application/zip",
        )

        logger.info(
            f"Successfully created memory-efficient controlled streaming ZIP: {file_key}"
        )

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
        def replace_urls(obj):
            if isinstance(obj, dict):
                return {k: replace_urls(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_urls(item) for item in obj]
            elif isinstance(obj, str) and obj in url_mapping:
                return url_mapping[obj]
            return obj

        return replace_urls(data)

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

    def _upload_data_only_zip(
        self,
        storage_client: CloudStorageClient,
        bucket_name: str,
        file_key: str,
        data: dict,
        resp_format: str = "json",
    ) -> None:
        """Upload a ZIP file containing only data (no attachments)."""

        data_files_generator = self._create_data_files(data, resp_format)
        data_files_list = list(
            data_files_generator
        )  # Convert generator to list for logging

        # Recreate the generator for the ZIP
        data_files_generator = self._create_data_files(data, resp_format)

        storage_client.put_object(
            bucket_name,
            file_key,
            stream_zip(self._convert_to_stream_zip_format(data_files_generator)),
            content_type="application/zip",
        )

        logger.info(
            f"Successfully created data-only ZIP: {file_key} with {len(data_files_list)} files"
        )

    def _create_zip_generator(
        self,
        data: dict,
        all_attachments: list[AttachmentProcessingInfo],
        storage_client: CloudStorageClient,
        bucket_name: str,
        max_workers: int,
        batch_size: int,
        resp_format: str = "json",
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Create a generator that yields files for the ZIP with minimal memory footprint."""

        # First yield data files
        yield from self._yield_data_files(data, resp_format, all_attachments)

        # Then yield attachments
        yield from self._yield_attachments(
            all_attachments, storage_client, bucket_name, batch_size
        )

    def _yield_data_files(
        self,
        data: dict,
        resp_format: str,
        all_attachments: Optional[list[AttachmentProcessingInfo]] = None,
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Yield data files in stream_zip format."""
        data_files_count = 0

        for data_file in self._create_data_files(data, resp_format, all_attachments):
            data_files_count += 1
            filename, content, _ = data_file
            content_bytes = content.getvalue()
            yield filename, datetime.now(), 0o644, _ZIP_32_TYPE(), iter([content_bytes])

    def _yield_attachments(
        self,
        all_attachments: list[AttachmentProcessingInfo],
        storage_client: CloudStorageClient,
        bucket_name: str,
        batch_size: int,
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Yield attachments in stream_zip format with true streaming from URLs."""
        attachment_files_count = 0

        for batch in self._get_attachment_batches(all_attachments, batch_size):
            for attachment_info in batch:
                attachment_files_count += 1
                yield from self._yield_single_attachment(
                    attachment_info, attachment_files_count, storage_client, bucket_name
                )

    def _yield_single_attachment(
        self,
        attachment_info: AttachmentProcessingInfo,
        file_number: int,
        storage_client: CloudStorageClient,
        bucket_name: str,
    ) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
        """Yield a single attachment in stream_zip format."""
        filename = attachment_info.attachment.file_name or f"attachment_{file_number}"

        if attachment_info.attachment.storage_key.startswith(("http://", "https://")):
            # True streaming from URL
            content_stream = self._create_url_stream(
                attachment_info.attachment.storage_key
            )
            yield filename, datetime.now(), 0o644, _ZIP_32_TYPE(), content_stream
        else:
            # Fallback for storage-based attachments
            try:
                content = storage_client.get_object(
                    bucket_name, attachment_info.attachment.storage_key
                )
                yield filename, datetime.now(), 0o644, _ZIP_32_TYPE(), iter([content])
            except Exception as e:
                logger.warning(
                    f"Failed to download attachment {filename} from storage: {e}"
                )

    def _create_url_stream(self, url: str) -> Iterable[bytes]:
        """Create a lazy generator that streams from URL when called."""

        def stream_generator() -> Iterable[bytes]:
            try:
                with requests.get(url, timeout=30, stream=True) as response:
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
            except Exception as e:
                logger.error(f"Failed to stream from URL {url}: {e}")
                raise StorageUploadError(f"Failed to stream from URL {url}: {e}") from e

        return stream_generator()

    def _get_attachment_batches(
        self, all_attachments: list[AttachmentProcessingInfo], batch_size: int
    ) -> list[list[AttachmentProcessingInfo]]:
        """Split attachments into batches for controlled processing."""
        return [
            all_attachments[i : i + batch_size]
            for i in range(0, len(all_attachments), batch_size)
        ]
