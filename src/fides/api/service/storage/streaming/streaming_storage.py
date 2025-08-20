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
from fides.api.service.storage.streaming.util import should_split_package

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def _convert_to_stream_zip_format(
    generator: Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
) -> Generator[Tuple[str, datetime, int, Any, Iterable[bytes]], None, None]:
    """Convert generator from (filename, BytesIO, metadata) to (filename, datetime, mode, method, content_iter) format.

    This adapter converts our internal generator format to the format expected by stream_zip.
    """
    for filename, content, metadata in generator:
        # Reset BytesIO position and get content
        content.seek(0)
        content_bytes = content.read()
        content.seek(0)  # Reset for potential reuse

        yield filename, datetime.now(), 0o644, _ZIP_32_TYPE(), iter([content_bytes])


def build_attachments_list(
    data: dict, config: PackageSplitConfig
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

            # Handle cases where attachments might be None or not a list
            if not isinstance(attachments, list):
                attachments = []

            attachment_count = len(attachments)

            # If a single item has more attachments than the limit, we need to split it
            if attachment_count > config.max_attachments:
                # Split the item into multiple sub-items
                for i in range(0, attachment_count, config.max_attachments):
                    sub_attachments = attachments[i : i + config.max_attachments]
                    sub_item = item.copy()
                    sub_item["attachments"] = sub_attachments
                    attachments_list.append((key, sub_item, len(sub_attachments)))
            else:
                attachments_list.append((key, item, attachment_count))

    return attachments_list


def split_data_into_packages(
    data: dict, config: Optional[PackageSplitConfig] = None
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
    all_items = build_attachments_list(data, config)

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


def _handle_package_splitting(
    data: dict,
    file_key: str,
    storage_client: CloudStorageClient,
    bucket_name: str,
    privacy_request: PrivacyRequest,
    max_workers: int,
    buffer_config: StreamingBufferConfig,
) -> None:
    """Handle splitting large datasets into multiple packages.

    Args:
        data: The data to split
        file_key: Base file key for the upload
        storage_client: Cloud storage client
        bucket_name: Target bucket name
        privacy_request: Privacy request context
        max_workers: Maximum parallel workers
        buffer_config: Buffer configuration

    """
    logger.info("Large dataset detected, splitting into multiple packages")
    packages = split_data_into_packages(data)
    logger.info("Split into {} packages", len(packages))

    # Process each package separately
    for i, package in enumerate(packages):
        package_key = f"{file_key}_part_{i+1}"
        logger.info("Processing package {}/{}: {}", i + 1, len(packages), package_key)

        stream_attachments_to_storage_zip(
            storage_client,
            bucket_name,
            package_key,
            package,
            privacy_request,
            max_workers,
            buffer_config,
        )


def _collect_and_validate_attachments(data: dict) -> List[AttachmentProcessingInfo]:
    """Collect and validate all attachments from the data.

    Args:
        data: The data dictionary containing items with attachments

    Returns:
        List of validated AttachmentProcessingInfo objects
    """
    all_attachments = []

    for key, value in data.items():
        # Check if value is iterable and has length
        try:
            if hasattr(value, "__iter__") and hasattr(value, "__len__"):
                value_len = int(len(value))
                if value_len > 0:
                    for idx, item in enumerate(value):
                        try:
                            # Check if item is a dict-like object before calling .get()
                            if hasattr(item, "get") and callable(
                                getattr(item, "get", None)
                            ):
                                attachments = item.get("attachments", [])
                                for attachment in attachments:
                                    # Check if attachment has required fields
                                    if "storage_key" not in attachment:
                                        error_msg = f"Attachment missing required field 'storage_key': {attachment}"
                                        logger.error(error_msg)
                                        continue

                                    # Validate attachment data using Pydantic model
                                    try:
                                        attachment_info = AttachmentInfo(**attachment)
                                        processing_info = AttachmentProcessingInfo(
                                            attachment=attachment_info,
                                            base_path=f"{key}/{idx + 1}/attachments",
                                            item=item,
                                        )
                                        all_attachments.append(processing_info)
                                    except (ValueError, TypeError, KeyError) as e:
                                        error_msg = f"Invalid attachment data: {e}"
                                        logger.error(error_msg)
                                        continue
                            else:
                                # Item is not dict-like, log and continue
                                error_msg = f"Item at index {idx} is not a dict-like object: {type(item)}"
                                logger.warning(error_msg)
                                continue
                        except (AttributeError, TypeError) as e:
                            # Handle mock objects or other types gracefully
                            error_msg = f"Failed to process item at index {idx}: {e}"
                            logger.warning(error_msg)
                            continue
        except (TypeError, ValueError) as e:
            # Handle cases where len() fails or comparison fails
            error_msg = f"Failed to process value for key '{key}': {e}"
            logger.warning(error_msg)
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
    storage_client: CloudStorageClient,
    data: dict,
    config: StorageUploadConfig,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[Any] = None,
    buffer_config: Optional[StreamingBufferConfig] = None,
    use_memory_efficient: bool = True,
    batch_size: int = 10,
) -> Optional[AnyHttpUrlString]:
    """Upload data to cloud storage using streaming for memory efficiency.

    This function implements true streaming from source to destination cloud storage,
    minimizing local memory usage by processing attachments as they're downloaded.

    Args:
        storage_client: Cloud storage client
        data: Data to upload
        config: Upload configuration
        privacy_request: Privacy request object
        document: Optional document (not yet implemented)
        buffer_config: Buffer configuration
        use_memory_efficient: Whether to use batch processing for minimal memory usage
        batch_size: Number of attachments to process in each batch (if use_memory_efficient=True)

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
            # Use memory-efficient streaming by default
            if use_memory_efficient:
                stream_attachments_to_storage_zip_memory_efficient(
                    storage_client,
                    config.bucket_name,
                    config.file_key,
                    data,
                    privacy_request,
                    config.max_workers,
                    buffer_config,
                    batch_size,
                )
            else:
                stream_attachments_to_storage_zip(
                    storage_client,
                    config.bucket_name,
                    config.file_key,
                    data,
                    privacy_request,
                    config.max_workers,
                    buffer_config,
                )

        elif config.resp_format == ResponseFormat.json.value:
            # Use memory-efficient streaming by default
            if use_memory_efficient:
                stream_attachments_to_storage_zip_memory_efficient(
                    storage_client,
                    config.bucket_name,
                    config.file_key,
                    data,
                    privacy_request,
                    config.max_workers,
                    buffer_config,
                    batch_size,
                )
            else:
                stream_attachments_to_storage_zip(
                    storage_client,
                    config.bucket_name,
                    config.file_key,
                    data,
                    privacy_request,
                    config.max_workers,
                    buffer_config,
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
    operation_name="stream attachments to storage ZIP",
    max_retries=2,
    base_delay=2.0,
    max_delay=30.0,
)
def stream_attachments_to_storage_zip(
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    data: dict,
    privacy_request: PrivacyRequest,
    max_workers: int = 5,
    buffer_config: Optional[StreamingBufferConfig] = None,
) -> None:
    """Stream attachments directly to storage using stream_zip with controlled concurrency.

    This function implements true streaming by yielding attachments as they're downloaded,
    using a sliding window approach to maintain only max_workers active downloads at any time.
    This prevents memory spikes and ensures efficient resource usage.

    Args:
        storage_client: Cloud storage client
        bucket_name: Bucket name for upload
        file_key: File key for the ZIP file
        data: Data containing attachments
        privacy_request: Privacy request object
        max_workers: Maximum number of parallel workers for downloads
        buffer_config: Buffer configuration

    """
    # Use default buffer config if none provided
    if buffer_config is None:
        buffer_config = StreamingBufferConfig()

    # Check if we should split into multiple packages
    if should_split_package(data):
        return _handle_package_splitting(
            data,
            file_key,
            storage_client,
            bucket_name,
            privacy_request,
            max_workers,
            buffer_config,
        )

    try:
        # Collect attachments first
        all_attachments = _collect_and_validate_attachments(data)

        if not all_attachments:
            logger.warning("No valid attachments found in data")

            # Create ZIP with just data files
            def files_to_zip() -> (
                Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
            ):
                # Add CSV/JSON data files only
                for key, value in data.items():
                    if isinstance(value, list) and value:
                        if key in ["data", "items", "records"]:
                            if any("attachments" in item for item in value):
                                data_content = json.dumps(value, default=str).encode(
                                    "utf-8"
                                )
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

            # Upload ZIP with just data files
            storage_client.put_object(
                bucket_name,
                file_key,
                stream_zip(_convert_to_stream_zip_format(files_to_zip())),
                content_type="application/zip",
            )

            logger.info("Successfully created ZIP file with data files only")
            return  # Exit early to avoid double upload

        # Create a controlled streaming generator with sliding window concurrency
        def controlled_streaming_generator() -> (
            Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
        ):
            """Generator that maintains controlled concurrency to prevent memory spikes."""
            active_futures = {}  # Only keep max_workers futures active at any time
            attachment_iter = iter(all_attachments)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit initial batch of futures to fill the window
                for _ in range(min(max_workers, len(all_attachments))):
                    try:
                        processing_info = next(attachment_iter)
                        future = executor.submit(
                            _download_attachment_parallel,
                            storage_client,
                            bucket_name,
                            processing_info.attachment,
                        )
                        active_futures[future] = processing_info
                    except StopIteration:
                        break

                # Process as they complete, maintaining controlled concurrency
                while active_futures:
                    # Wait for any future to complete
                    done_future = None
                    for future in active_futures:
                        if future.done():
                            done_future = future
                            break

                    if done_future is None:
                        # No futures are done yet, wait for the first one
                        done_future = next(iter(active_futures))
                        try:
                            done_future.result()  # This will wait for completion
                        except Exception as e:
                            # Handle download failure gracefully
                            processing_info = active_futures.pop(done_future)
                            error_msg = f"Failed to download attachment {processing_info.attachment.file_name or 'unknown'}: {e}"
                            logger.warning(error_msg)
                            # Don't yield this attachment - it will be skipped
                            continue

                    # Process the completed future
                    processing_info = active_futures.pop(done_future)

                    try:
                        filename, content = done_future.result()
                        logger.debug(
                            "Downloaded attachment: {} ({:.2f} MB)",
                            filename,
                            len(content) / (1024 * 1024),
                        )

                        # Yield the attachment immediately - no memory accumulation
                        yield filename, BytesIO(content), {}

                    except Exception as e:
                        # Handle download failures gracefully - log error and continue
                        error_msg = f"Failed to download attachment {processing_info.attachment.file_name or 'unknown'}: {e}"
                        logger.warning(error_msg)
                        # Don't yield this attachment - it will be skipped

                    # Submit next attachment to maintain concurrency (sliding window)
                    try:
                        next_processing_info = next(attachment_iter)
                        next_future = executor.submit(
                            _download_attachment_parallel,
                            storage_client,
                            bucket_name,
                            next_processing_info.attachment,
                        )
                        active_futures[next_future] = next_processing_info
                    except StopIteration:
                        # No more attachments to process, let remaining futures complete
                        pass

        logger.info(
            "Starting controlled streaming ZIP creation with {} attachments",
            len(all_attachments),
        )

        def files_to_zip() -> (
            Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
        ):
            """Generator that yields (filename, file-like object, metadata) tuples for stream_zip."""
            # Add CSV/JSON data files first
            for key, value in data.items():
                if isinstance(value, list) and value:
                    if key in ["data", "items", "records"]:
                        if any("attachments" in item for item in value):
                            data_content = json.dumps(value, default=str).encode(
                                "utf-8"
                            )
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

            # Stream attachments with controlled concurrency - no memory accumulation
            for filename, content, metadata in controlled_streaming_generator():
                yield filename, content, metadata

        # Upload the ZIP file using stream_zip with controlled streaming generator
        storage_client.put_object(
            bucket_name,
            file_key,
            stream_zip(_convert_to_stream_zip_format(files_to_zip())),
            content_type="application/zip",
        )

        logger.info(
            "Successfully created and uploaded controlled streaming ZIP file: {}",
            file_key,
        )

    except (ValueError, AttributeError) as e:
        # Handle configuration or validation errors
        error_msg = f"Configuration error creating controlled streaming ZIP file: {e}"
        logger.error(error_msg)
        raise StorageUploadError(error_msg) from e
    except Exception as e:
        # Handle unexpected errors
        error_msg = (
            f"Failed to create controlled streaming ZIP file using stream_zip: {e}"
        )
        logger.error(error_msg)
        raise StorageUploadError(error_msg) from e


@retry_cloud_storage_operation(
    provider="cloud storage",
    operation_name="stream attachments to storage ZIP (memory efficient)",
    max_retries=2,
    base_delay=2.0,
    max_delay=30.0,
)
def stream_attachments_to_storage_zip_memory_efficient(
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

    all_attachments = _collect_and_validate_attachments(data)

    if not all_attachments:
        # Handle case with no attachments (same as before)
        def files_to_zip() -> (
            Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
        ):
            for key, value in data.items():
                if isinstance(value, list) and value:
                    if key in ["data", "items", "records"]:
                        if any("attachments" in item for item in value):
                            data_content = json.dumps(value, default=str).encode(
                                "utf-8"
                            )
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

        storage_client.put_object(
            bucket_name,
            file_key,
            stream_zip(_convert_to_stream_zip_format(files_to_zip())),
            content_type="application/zip",
        )
        return  # Exit early to avoid double upload

    logger.info(
        "Starting memory-efficient controlled streaming ZIP creation with {} attachments in batches of {}",
        len(all_attachments),
        batch_size,
    )

    def controlled_batch_generator() -> (
        Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
    ):
        """Generator that processes attachments in controlled batches with sliding window concurrency."""
        for i in range(0, len(all_attachments), batch_size):
            batch = all_attachments[i : i + batch_size]
            batch_workers = min(max_workers, len(batch))

            logger.debug(
                "Processing batch {}/{} with {} workers for {} attachments",
                (i // batch_size) + 1,
                (len(all_attachments) + batch_size - 1) // batch_size,
                batch_workers,
                len(batch),
            )

            # Process this batch with controlled concurrency
            active_futures = {}  # Only keep batch_workers futures active
            batch_iter = iter(batch)

            with ThreadPoolExecutor(max_workers=batch_workers) as executor:
                # Submit initial futures to fill the window
                for _ in range(min(batch_workers, len(batch))):
                    try:
                        processing_info = next(batch_iter)
                        future = executor.submit(
                            _download_attachment_parallel,
                            storage_client,
                            bucket_name,
                            processing_info.attachment,
                        )
                        active_futures[future] = processing_info
                    except StopIteration:
                        break

                # Process batch with controlled concurrency
                while active_futures:
                    # Wait for any future to complete
                    done_future = None
                    for future in active_futures:
                        if future.done():
                            done_future = future
                            break

                    if done_future is None:
                        # No futures are done yet, wait for the first one
                        done_future = next(iter(active_futures))
                        try:
                            done_future.result()  # This will wait for completion
                        except Exception as e:
                            # Handle download failure gracefully
                            processing_info = active_futures.pop(done_future)
                            error_msg = f"Failed to download attachment {processing_info.attachment.file_name or 'unknown'}: {e}"
                            logger.warning(error_msg)
                            # Don't yield this attachment - it will be skipped
                            continue

                    # Process the completed future
                    processing_info = active_futures.pop(done_future)

                    try:
                        filename, content = done_future.result()

                        logger.debug(
                            "Processed attachment: {} ({:.2f} MB)",
                            filename,
                            len(content) / (1024 * 1024),
                        )

                        # Yield immediately and let garbage collection handle cleanup
                        yield filename, BytesIO(content), {}

                    except Exception as e:
                        # Handle download failures gracefully - log error and continue
                        error_msg = f"Failed to download attachment {processing_info.attachment.file_name or 'unknown'}: {e}"
                        logger.warning(error_msg)
                        # Don't yield this attachment - it will be skipped

                    # Submit next attachment to maintain concurrency within the batch
                    try:
                        next_processing_info = next(batch_iter)
                        next_future = executor.submit(
                            _download_attachment_parallel,
                            storage_client,
                            bucket_name,
                            next_processing_info.attachment,
                        )
                        active_futures[next_future] = next_processing_info
                    except StopIteration:
                        # No more attachments in this batch, let remaining futures complete
                        pass

            # Log batch completion for monitoring
            logger.debug(
                "Completed batch {}/{} ({:.1f}% complete)",
                (i // batch_size) + 1,
                (len(all_attachments) + batch_size - 1) // batch_size,
                (i + len(batch)) / len(all_attachments) * 100,
            )

    def files_to_zip_batch() -> (
        Generator[Tuple[str, BytesIO, Dict[str, Any]], None, None]
    ):
        """Generator that yields files for stream_zip with minimal memory footprint."""
        # Add data files first
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

        # Stream attachments in controlled batches - memory is freed after each batch
        for filename, content, metadata in controlled_batch_generator():
            yield filename, content, metadata

    # Upload using the memory-efficient controlled generator
    storage_client.put_object(
        bucket_name,
        file_key,
        stream_zip(_convert_to_stream_zip_format(files_to_zip_batch())),
        content_type="application/zip",
    )

    logger.info(
        "Successfully created memory-efficient controlled streaming ZIP: {}", file_key
    )


@retry_cloud_storage_operation(
    provider="cloud storage",
    operation_name="download attachment",
    max_retries=3,
    base_delay=1.0,
    max_delay=15.0,
)
def _download_attachment_parallel(
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
        file_content = storage_client.get_object(bucket_name, attachment.storage_key)

        return filename, file_content

    except (ValueError, AttributeError) as e:
        # Handle configuration or validation errors during download
        # These are permanent errors that shouldn't be retried
        raise PermanentError(
            f"Configuration error downloading attachment {attachment.file_name}: {e}"
        ) from e
    except Exception as e:
        # Check if this is a transient error that should be retried
        if is_transient_error(e) or is_s3_transient_error(e):
            raise TransientError(
                f"Transient error downloading attachment {attachment.file_name}: {e}"
            ) from e
        else:
            # Handle unexpected errors during download
            raise StorageUploadError(
                f"Failed to download attachment {attachment.file_name}: {e}"
            ) from e
