from __future__ import annotations

import csv
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List, Optional, Tuple

from fideslang.validation import AnyHttpUrlString
from loguru import logger
from stream_zip import _ZIP_32_TYPE, stream_zip

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.dsr_storage import (
    stream_html_dsr_report_to_storage_multipart,
)
from fides.api.service.storage.streaming.retry import (
    PermanentError,
    TransientError,
    is_s3_transient_error,
    is_transient_error,
    retry_cloud_storage_operation,
)
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
        self, generator: Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
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

        packages: List[Dict[str, Any]] = []
        package_attachment_counts: List[int] = []

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

    def _collect_and_validate_attachments(
        self, data: dict
    ) -> List[AttachmentProcessingInfo]:
        """Collect and validate all attachments from the data.

        Args:
            data: The data dictionary containing items with attachments

        Returns:
            List of validated AttachmentProcessingInfo objects
        """
        all_attachments = []

        for key, value in data.items():
            if not isinstance(value, list) or not value:
                continue

            for idx, item in enumerate(value):
                if not isinstance(item, dict):
                    continue

                attachments = item.get("attachments", [])
                if not isinstance(attachments, list):
                    continue

                for attachment in attachments:
                    if (
                        not isinstance(attachment, dict)
                        or "storage_key" not in attachment
                    ):
                        continue

                    try:
                        attachment_info = AttachmentInfo(**attachment)
                        processing_info = AttachmentProcessingInfo(
                            attachment=attachment_info,
                            base_path=f"{key}/{idx + 1}/attachments",
                            item=item,
                        )
                        all_attachments.append(processing_info)
                    except (ValueError, TypeError, KeyError):
                        # Invalid attachment data, skip it
                        continue

        return all_attachments

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
            presigned_url

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
            self._upload_data_only_zip(storage_client, bucket_name, file_key, data)
            return

        logger.info(
            "Starting memory-efficient controlled streaming ZIP creation with {} attachments in batches of {}",
            len(all_attachments),
            batch_size,
        )

        # Create the ZIP file with data and attachments
        zip_generator = self._create_zip_generator(
            data, all_attachments, storage_client, bucket_name, max_workers, batch_size
        )

        storage_client.put_object(
            bucket_name,
            file_key,
            stream_zip(self._convert_to_stream_zip_format(zip_generator)),
            content_type="application/zip",
        )

        logger.info(
            "Successfully created memory-efficient controlled streaming ZIP: {}",
            file_key,
        )

    def _create_data_files(
        self,
        data: dict,
    ) -> Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]:
        """Create data files (JSON/CSV) from the input data."""
        for key, value in data.items():
            if isinstance(value, list) and value:
                if key in ["data", "items", "records"]:
                    if any("attachments" in item for item in value):
                        data_content = json.dumps(value, default=str).encode("utf-8")
                        yield f"{key}.json", BytesIO(data_content), {}
                    else:
                        csv_buffer = StringIO()
                        if value:
                            writer = csv.DictWriter(
                                csv_buffer, fieldnames=value[0].keys()
                            )
                            writer.writeheader()
                            writer.writerows(value)
                        data_content = csv_buffer.getvalue().encode("utf-8")
                        yield f"{key}.csv", BytesIO(data_content), {}

    def _upload_data_only_zip(
        self,
        storage_client: CloudStorageClient,
        bucket_name: str,
        file_key: str,
        data: dict,
    ) -> None:
        """Upload a ZIP file containing only data (no attachments)."""
        storage_client.put_object(
            bucket_name,
            file_key,
            stream_zip(
                self._convert_to_stream_zip_format(self._create_data_files(data))
            ),
            content_type="application/zip",
        )

    def _process_attachment_batch(
        self,
        batch: List[AttachmentProcessingInfo],
        storage_client: CloudStorageClient,
        bucket_name: str,
        max_workers: int,
    ) -> Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]:
        """Process a single batch of attachments with controlled concurrency."""
        batch_workers = min(max_workers, len(batch))

        logger.debug(
            "Processing batch with {} workers for {} attachments",
            batch_workers,
            len(batch),
        )

        with ThreadPoolExecutor(max_workers=batch_workers) as executor:
            # Submit all attachments in the batch
            future_to_info = {
                executor.submit(
                    self._download_attachment_parallel,
                    storage_client,
                    bucket_name,
                    info.attachment,
                ): info
                for info in batch
            }

            # Process completed futures as they finish
            for future in future_to_info:
                try:
                    filename, content = future.result()
                    logger.debug(
                        "Processed attachment: {} ({:.2f} MB)",
                        filename,
                        len(content) / (1024 * 1024),
                    )
                    yield filename, BytesIO(content), {}

                except Exception as e:
                    # Handle download failures gracefully - log error and continue
                    processing_info = future_to_info[future]
                    error_msg = f"Failed to download attachment {processing_info.attachment.file_name or 'unknown'}: {e}"
                    logger.warning(error_msg)
                    # Don't yield this attachment - it will be skipped

    def _create_zip_generator(
        self,
        data: dict,
        all_attachments: List[AttachmentProcessingInfo],
        storage_client: CloudStorageClient,
        bucket_name: str,
        max_workers: int,
        batch_size: int,
    ) -> Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]:
        """Create a generator that yields files for the ZIP with minimal memory footprint."""

        # First yield data files
        yield from self._create_data_files(data)

        # Then yield attachments in controlled batches with progress tracking
        total_batches = (len(all_attachments) + batch_size - 1) // batch_size

        for batch_num, batch in enumerate(
            self._get_attachment_batches(all_attachments, batch_size), 1
        ):
            logger.debug(
                "Processing batch {}/{} ({:.1f}% complete)",
                batch_num,
                total_batches,
                (batch_num * batch_size) / len(all_attachments) * 100,
            )

            yield from self._process_attachment_batch(
                batch, storage_client, bucket_name, max_workers
            )

    def _get_attachment_batches(
        self, all_attachments: List[AttachmentProcessingInfo], batch_size: int
    ) -> List[List[AttachmentProcessingInfo]]:
        """Split attachments into batches for controlled processing."""
        return [
            all_attachments[i : i + batch_size]
            for i in range(0, len(all_attachments), batch_size)
        ]

    @retry_cloud_storage_operation(
        provider="cloud storage",
        operation_name="download attachment",
        max_retries=3,
        base_delay=1.0,
        max_delay=15.0,
    )
    def _download_attachment_parallel(
        self,
        storage_client: CloudStorageClient,
        bucket_name: str,
        attachment: AttachmentInfo,
    ) -> Tuple[str, bytes]:
        """Download a single attachment in parallel.

        Args:
            storage_client: Cloud storage client
            bucket_name: Bucket name
            attachment: Attachment info

        Returns:
            Tuple of (filename, file_content)

        Raises:
            Exception: If download fails (will be handled by caller)
        """
        try:
            filename = attachment.file_name or "attachment"

            # Get the file content from storage
            file_content = storage_client.get_object(
                bucket_name, attachment.storage_key
            )

            return filename, file_content

        except (ValueError, AttributeError) as e:
            # Handle configuration or validation errors during download
            # These are permanent errors that shouldn't be retried
            raise PermanentError(
                f"Configuration error downloading attachment {attachment.file_name}: {e}"
            ) from e
        except PermanentError:
            # Re-raise permanent errors without wrapping
            raise
        except Exception as e:
            # Check if this is a transient error that should be retried
            if is_transient_error(e) or is_s3_transient_error(e):
                raise TransientError(
                    f"Transient error downloading attachment {attachment.file_name}: {e}"
                ) from e

            # Handle unexpected errors during download
            raise StorageUploadError(
                f"Failed to download attachment {attachment.file_name}: {e}"
            ) from e
