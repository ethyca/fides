from __future__ import annotations

import csv
import json
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.cloud_storage_client import (
    CloudStorageClient,
    ProgressCallback,
)
from fides.api.service.storage.streaming.dsr_storage import (
    stream_html_dsr_report_to_storage_multipart,
)
from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    AttachmentProcessingInfo,
    ChunkDownloadConfig,
    PackageSplitConfig,
    ProcessingMetrics,
    StorageUploadConfig,
    StreamingBufferConfig,
)
from fides.api.service.storage.streaming.streaming_zip_util import (
    create_central_directory_parts,
    create_data_descriptor,
    create_local_file_header,
)
from fides.api.service.storage.streaming.util import (
    adaptive_chunk_size,
    should_split_package,
)

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


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
    all_items = []
    for key, value in data.items():
        if isinstance(value, list) and value:
            for item in value:
                attachments = item.get("attachments", [])
                attachment_count = len(attachments)

                # If a single item has more attachments than the limit, we need to split it
                if attachment_count > config.max_attachments:
                    # Split the item into multiple sub-items
                    for i in range(0, attachment_count, config.max_attachments):
                        sub_attachments = attachments[i : i + config.max_attachments]
                        sub_item = item.copy()
                        sub_item["attachments"] = sub_attachments
                        all_items.append((key, sub_item, len(sub_attachments)))
                else:
                    all_items.append((key, item, attachment_count))

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


def _calculate_data_metrics(data: dict) -> ProcessingMetrics:
    """Calculate total metrics for the data before processing.

    Args:
        data: The data dictionary containing items with attachments

    Returns:
        ProcessingMetrics with total_attachments and total_bytes populated
    """
    metrics = ProcessingMetrics()

    for value in data.values():
        if hasattr(value, "__iter__") and hasattr(value, "__len__") and len(value) > 0:
            for item in value:
                try:
                    attachments = item.get("attachments", [])
                    metrics.total_attachments += len(attachments)
                    metrics.total_bytes += sum(
                        att.get("size", 1024 * 1024) for att in attachments
                    )
                except (AttributeError, TypeError):
                    # Handle mock objects or other types gracefully
                    pass

    return metrics


def _handle_package_splitting(
    data: dict,
    file_key: str,
    storage_client: CloudStorageClient,
    bucket_name: str,
    privacy_request: PrivacyRequest,
    max_workers: int,
    progress_callback: Optional[ProgressCallback],
    buffer_config: StreamingBufferConfig,
) -> ProcessingMetrics:
    """Handle splitting large datasets into multiple packages.

    Args:
        data: The data to split
        file_key: Base file key for the upload
        storage_client: Cloud storage client
        bucket_name: Target bucket name
        privacy_request: Privacy request context
        max_workers: Maximum parallel workers
        progress_callback: Optional progress callback
        buffer_config: Buffer configuration

    Returns:
        Combined metrics from all packages
    """
    logger.info("Large dataset detected, splitting into multiple packages")
    packages = split_data_into_packages(data)
    logger.info("Split into {} packages", len(packages))

    # Process each package separately
    all_metrics = []
    for i, package in enumerate(packages):
        package_key = f"{file_key}_part_{i+1}"
        logger.info("Processing package {}/{}: {}", i + 1, len(packages), package_key)

        package_metrics = stream_attachments_to_storage_zip(
            storage_client,
            bucket_name,
            package_key,
            package,
            privacy_request,
            max_workers,
            progress_callback,
            buffer_config,
        )
        all_metrics.append(package_metrics)

    # Combine metrics from all packages
    combined_metrics = ProcessingMetrics()
    # Calculate total metrics from original data to avoid double-counting
    original_metrics = _calculate_data_metrics(data)
    combined_metrics.total_attachments = original_metrics.total_attachments
    combined_metrics.total_bytes = original_metrics.total_bytes

    for pm in all_metrics:
        combined_metrics.processed_attachments += pm.processed_attachments
        combined_metrics.processed_bytes += pm.processed_bytes
        combined_metrics.errors.extend(pm.errors)

    return combined_metrics


def _collect_and_validate_attachments(
    data: dict, metrics: ProcessingMetrics
) -> List[AttachmentProcessingInfo]:
    """Collect and validate all attachments from the data.

    Args:
        data: The data dictionary containing items with attachments
        metrics: Processing metrics to track errors

    Returns:
        List of validated AttachmentProcessingInfo objects
    """
    all_attachments = []

    for key, value in data.items():
        # Check if value is iterable and has length
        try:
            if hasattr(value, "__iter__") and hasattr(value, "__len__"):
                # Convert to int to avoid MagicMock comparison issues
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
                                    if "s3_key" not in attachment:
                                        error_msg = f"Attachment missing required field 's3_key': {attachment}"
                                        logger.error(error_msg)
                                        metrics.errors.append(error_msg)
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
                                        metrics.errors.append(error_msg)
                                        continue
                            else:
                                # Item is not dict-like, log and continue
                                error_msg = f"Item at index {idx} is not a dict-like object: {type(item)}"
                                logger.warning(error_msg)
                                metrics.errors.append(error_msg)
                                continue
                        except (AttributeError, TypeError) as e:
                            # Handle mock objects or other types gracefully
                            error_msg = f"Failed to process item at index {idx}: {e}"
                            logger.warning(error_msg)
                            metrics.errors.append(error_msg)
                            continue
        except (TypeError, ValueError) as e:
            # Handle cases where len() fails or comparison fails
            error_msg = f"Failed to process value for key '{key}': {e}"
            logger.warning(error_msg)
            metrics.errors.append(error_msg)
            continue

    return all_attachments


def _serialize_item_data(
    item: Any,
    key: str,
    idx: int,
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    upload_id: str,
    parts: List[Any],
    part_number: int,
    file_entries: List[Tuple[str, int, int, int]],
    current_offset: int,
    metrics: ProcessingMetrics,
) -> Tuple[int, int]:
    """Serialize item data to CSV or JSON and upload as zip part.

    Args:
        item: The item to serialize
        key: Data key
        idx: Item index
        storage_client: Cloud storage client
        bucket_name: Target bucket name
        file_key: File key for upload
        upload_id: Multipart upload ID
        parts: List of uploaded parts
        part_number: Current part number
        file_entries: File entries for central directory
        current_offset: Current offset in ZIP file
        metrics: Processing metrics to track errors

    Returns:
        Tuple of (updated_part_number, updated_current_offset)
    """
    filename = f"{key}/{idx + 1}/item"

    # Try CSV first for dict items - handle both real dicts and mock objects
    try:
        if (
            hasattr(item, "keys")
            and hasattr(item, "values")
            and hasattr(item, "__len__")
        ):
            # Check if it's a dict-like object (including mocks)
            try:
                item_len = int(len(item))
                if item_len > 0:
                    try:
                        # Create CSV data in memory (small, acceptable)
                        csv_buffer = StringIO()
                        csv_writer = csv.writer(csv_buffer)

                        # Write header - ensure keys are strings and handle any encoding issues
                        header = [str(k) for k in item.keys()]
                        csv_writer.writerow(header)
                        # Write data - ensure values are strings
                        row_data = [str(v) for v in item.values()]
                        csv_writer.writerow(row_data)

                        csv_buffer.seek(0)
                        csv_data = csv_buffer.getvalue().encode("utf-8")

                        # Create zip part for CSV data
                        csv_filename = f"{filename}.csv"
                        csv_crc32 = zlib.crc32(csv_data)
                        zip_part_data = create_zip_part_for_chunk(
                            csv_data,
                            csv_filename,
                            True,  # First chunk
                            True,  # Last chunk
                            len(csv_data),
                            csv_crc32,
                        )

                        # Upload CSV zip part to storage
                        part = storage_client.upload_part(
                            bucket_name,
                            file_key,
                            upload_id,
                            part_number,
                            zip_part_data,
                        )
                        parts.append(part)

                        # Track file entry for central directory
                        file_entries.append(
                            (csv_filename, len(csv_data), current_offset, csv_crc32)
                        )
                        current_offset += len(zip_part_data)
                        part_number += 1

                        return part_number, current_offset

                    except (TypeError, UnicodeEncodeError, csv.Error) as e:
                        # If CSV writing failed, fall back to JSON
                        logger.warning(
                            f"CSV writing failed for item {key}/{idx + 1}, falling back to JSON: {e}"
                        )
                        return _serialize_item_as_json(
                            item,
                            filename,
                            storage_client,
                            bucket_name,
                            file_key,
                            upload_id,
                            parts,
                            part_number,
                            file_entries,
                            current_offset,
                            metrics,
                        )
            except (TypeError, ValueError) as e:
                # Handle cases where len() fails or comparison fails
                logger.warning(
                    f"Failed to determine length for item {key}/{idx + 1}, falling back to JSON: {e}"
                )
                return _serialize_item_as_json(
                    item,
                    filename,
                    storage_client,
                    bucket_name,
                    file_key,
                    upload_id,
                    parts,
                    part_number,
                    file_entries,
                    current_offset,
                    metrics,
                )
    except (TypeError, UnicodeEncodeError, csv.Error, AttributeError) as e:
        # If CSV writing failed, fall back to JSON
        logger.warning(
            f"CSV writing failed for item {key}/{idx + 1}, falling back to JSON: {e}"
        )
        return _serialize_item_as_json(
            item,
            filename,
            storage_client,
            bucket_name,
            file_key,
            upload_id,
            parts,
            part_number,
            file_entries,
            current_offset,
            metrics,
        )

    # Handle non-dict items or fallback to JSON
    return _serialize_item_as_json(
        item,
        filename,
        storage_client,
        bucket_name,
        file_key,
        upload_id,
        parts,
        part_number,
        file_entries,
        current_offset,
        metrics,
    )


def _serialize_item_as_json(
    item: Any,
    filename: str,
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    upload_id: str,
    parts: List[Any],
    part_number: int,
    file_entries: List[Tuple[str, int, int, int]],
    current_offset: int,
    metrics: ProcessingMetrics,
) -> Tuple[int, int]:
    """Serialize item as JSON and upload as zip part.

    Args:
        item: The item to serialize
        filename: Base filename (without extension)
        storage_client: Cloud storage client
        bucket_name: Target bucket name
        file_key: File key for upload
        upload_id: Multipart upload ID
        parts: List of uploaded parts
        part_number: Current part number
        file_entries: File entries for central directory
        current_offset: Current offset in ZIP file
        metrics: Processing metrics to track errors

    Returns:
        Tuple of (updated_part_number, updated_current_offset)
    """
    try:
        item_json = json.dumps(item, default=str)
        json_data = item_json.encode("utf-8")

        # Create zip part for JSON data
        json_filename = f"{filename}.json"
        json_crc32 = zlib.crc32(json_data)
        zip_part_data = create_zip_part_for_chunk(
            json_data,
            json_filename,
            True,  # First chunk
            True,  # Last chunk
            len(json_data),
            json_crc32,
        )

        # Upload JSON zip part to storage
        part = storage_client.upload_part(
            bucket_name,
            file_key,
            upload_id,
            part_number,
            zip_part_data,
        )
        parts.append(part)

        # Track file entry for central directory
        file_entries.append((json_filename, len(json_data), current_offset, json_crc32))
        current_offset += len(zip_part_data)
        part_number += 1

        return part_number, current_offset

    except (TypeError, UnicodeEncodeError, ValueError) as e:
        logger.error(f"Failed to serialize item {filename}: {e}")
        metrics.errors.append(f"Failed to serialize item {filename}: {e}")
        return part_number, current_offset


def _process_item_data(
    data: dict,
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    upload_id: str,
    parts: List[Any],
    part_number: int,
    file_entries: List[Tuple[str, int, int, int]],
    current_offset: int,
    metrics: ProcessingMetrics,
) -> Tuple[int, int]:
    """Process all item data and serialize to zip parts.

    Args:
        data: The data dictionary containing items
        storage_client: Cloud storage client
        bucket_name: Target bucket name
        file_key: File key for upload
        upload_id: Multipart upload ID
        parts: List of uploaded parts
        part_number: Current part number
        file_entries: File entries for central directory
        current_offset: Current offset in ZIP file
        metrics: Processing metrics to track errors

    Returns:
        Tuple of (updated_part_number, updated_current_offset)
    """
    for key, value in data.items():
        if hasattr(value, "__iter__") and hasattr(value, "__len__") and len(value) > 0:
            for idx, item in enumerate(value):
                if item:  # Only process non-empty items
                    part_number, current_offset = _serialize_item_data(
                        item,
                        key,
                        idx,
                        storage_client,
                        bucket_name,
                        file_key,
                        upload_id,
                        parts,
                        part_number,
                        file_entries,
                        current_offset,
                        metrics,
                    )

    return part_number, current_offset


def _complete_multipart_upload(
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    upload_id: str,
    parts: List[Any],
    part_number: int,
    file_entries: List[Tuple[str, int, int, int]],
    current_offset: int,
) -> None:
    """Complete the multipart upload with central directory.

    Args:
        storage_client: Cloud storage client
        bucket_name: Target bucket name
        file_key: File key for upload
        upload_id: Multipart upload ID
        parts: List of uploaded parts
        part_number: Current part number
        file_entries: File entries for central directory
        current_offset: Current offset in ZIP file
    """
    if parts:
        # Create central directory
        central_dir_parts = create_central_directory_parts(file_entries, current_offset)

        # Upload central directory parts
        for central_dir_part in central_dir_parts:
            part = storage_client.upload_part(
                bucket_name, file_key, upload_id, part_number, central_dir_part
            )
            parts.append(part)
            part_number += 1

        storage_client.complete_multipart_upload(
            bucket_name, file_key, upload_id, parts
        )
    else:
        # If no parts were uploaded, complete with empty parts list
        storage_client.complete_multipart_upload(bucket_name, file_key, upload_id, [])


def stream_attachments_to_storage_zip(
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    data: dict,
    privacy_request: PrivacyRequest,
    max_workers: int = 5,
    progress_callback: Optional[ProgressCallback] = None,
    buffer_config: Optional[StreamingBufferConfig] = None,
) -> ProcessingMetrics:
    """Stream attachments directly to cloud storage as zip parts without building in memory.

    This implements true streaming with:
    1. Direct download -> upload streaming (no memory accumulation)
    2. Parallel processing of multiple attachments
    3. Adaptive chunk sizes based on file size
    4. Progress tracking and comprehensive metrics
    5. Automatic package splitting for large datasets
    6. Robust error handling and retry logic
    7. Cloud-agnostic storage operations
    8. Memory usage limited to individual chunk size (~1-5MB max)
    """
    # Use default buffer config if none provided
    if buffer_config is None:
        buffer_config = StreamingBufferConfig()

    # Initialize metrics and calculate totals
    metrics = _calculate_data_metrics(data)

    logger.info(
        "Starting true streaming processing of {} attachments ({:.2f} GB total)",
        metrics.total_attachments,
        metrics.total_bytes / (1024**3),
    )

    # Check if we should split into multiple packages
    if should_split_package(data):
        return _handle_package_splitting(
            data,
            file_key,
            storage_client,
            bucket_name,
            privacy_request,
            max_workers,
            progress_callback,
            buffer_config,
        )

    # Initiate multipart upload for the zip file
    upload_id = None
    parts: List[Any] = []
    part_number = 1

    # Track file information for central directory
    file_entries: List[Tuple[str, int, int, int]] = (
        []
    )  # List of (filename, size, offset, crc32) tuples
    current_offset = 0

    try:
        response = storage_client.create_multipart_upload(
            bucket_name, file_key, "application/zip"
        )
        upload_id = response.upload_id

        # Collect and validate all attachments
        all_attachments = _collect_and_validate_attachments(data, metrics)

        # Check if we have any valid attachments to process
        if not all_attachments:
            logger.warning("No valid attachments found in data")
            # Still complete the upload but with no attachment content
            if upload_id:
                # Complete multipart upload with no parts
                storage_client.complete_multipart_upload(
                    bucket_name, file_key, upload_id, []
                )
            return metrics

        # Create upload context for coordination
        upload_context: Dict[str, Any] = {
            "storage_client": storage_client,
            "bucket_name": bucket_name,
            "file_key": file_key,
            "upload_id": upload_id,
            "parts": parts,
            "part_number": part_number,
            "lock": threading.Lock(),  # Thread-safe coordination
            "file_entries": file_entries,  # Track file entries for central directory
            "current_offset": current_offset,  # Track current offset in ZIP file
        }

        # Process attachments in parallel with true streaming
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all attachment processing tasks
            future_to_attachment = {
                executor.submit(
                    stream_single_attachment_to_storage_streaming,
                    upload_context,
                    processing_info.attachment,
                    processing_info.base_path,
                    metrics,
                    progress_callback,
                    buffer_config,
                ): processing_info
                for processing_info in all_attachments
            }

            # Process completed tasks
            for future in as_completed(future_to_attachment):
                processing_info: AttachmentProcessingInfo = future_to_attachment[future]
                try:
                    attachment_metrics = future.result()
                    metrics.processed_attachments += 1
                    metrics.processed_bytes += attachment_metrics.get(
                        "processed_bytes", 0
                    )

                    # Update progress
                    if progress_callback:
                        progress_callback(metrics)

                    logger.debug(
                        "Completed attachment {}/{}: {}",
                        metrics.processed_attachments,
                        metrics.total_attachments,
                        processing_info.attachment.file_name or "unknown",
                    )

                except (
                    StorageUploadError,
                    OSError,
                    ConnectionError,
                    TimeoutError,
                ) as e:
                    error_msg = f"Failed to process attachment {processing_info.attachment.file_name or 'unknown'}: {e}"
                    logger.error(error_msg)
                    metrics.errors.append(error_msg)

        # Update parts and part_number from context
        parts = upload_context["parts"]
        part_number = upload_context["part_number"]

        # Process item data (CSV/JSON serialization)
        part_number, current_offset = _process_item_data(
            data,
            storage_client,
            bucket_name,
            file_key,
            upload_id,
            parts,
            part_number,
            file_entries,
            current_offset,
            metrics,
        )

        # Complete multipart upload with central directory
        _complete_multipart_upload(
            storage_client,
            bucket_name,
            file_key,
            upload_id,
            parts,
            part_number,
            file_entries,
            current_offset,
        )

        logger.info(
            "Completed true streaming zip upload with {} parts in {:.2f}s",
            len(parts),
            metrics.elapsed_time,
        )

    except (
        StorageUploadError,
        OSError,
        ConnectionError,
        TimeoutError,
        ValueError,
    ) as e:
        # Abort multipart upload on failure if we have an upload_id
        if upload_id:
            try:
                storage_client.abort_multipart_upload(bucket_name, file_key, upload_id)
            except (StorageUploadError, OSError, ConnectionError) as abort_error:
                logger.warning("Failed to abort multipart upload: {}", abort_error)
        raise e

    return metrics


def stream_single_attachment_to_storage_streaming(
    upload_context: dict,
    attachment: AttachmentInfo,
    base_path: str,
    metrics: ProcessingMetrics,
    progress_callback: Optional[ProgressCallback] = None,
    buffer_config: Optional[StreamingBufferConfig] = None,
) -> dict[str, Any]:
    """Stream a single attachment directly to cloud storage without building zip in memory.

    This function downloads chunks and immediately uploads them to storage as zip parts,
    maintaining only a small buffer for the current chunk being processed.
    """
    # Use default buffer config if none provided
    if buffer_config is None:
        buffer_config = StreamingBufferConfig()

    storage_client = upload_context["storage_client"]
    bucket_name = upload_context["bucket_name"]
    file_key = upload_context["file_key"]
    upload_id = upload_context["upload_id"]

    source_key = attachment.s3_key
    filename = attachment.file_name or "attachment"

    # Update current attachment in metrics
    logger.debug("Setting metrics.current_attachment to: {}", filename)
    metrics.current_attachment = filename
    logger.debug("Setting metrics.current_attachment_progress to: 0.0")
    metrics.current_attachment_progress = 0.0

    try:
        # Get the object to determine its size
        head_response = storage_client.get_object_head(bucket_name, source_key)
        file_size = head_response["ContentLength"]

        # Use adaptive chunk size based on file size
        chunk_size = adaptive_chunk_size(file_size)
        total_chunks = (file_size + chunk_size - 1) // chunk_size

        logger.debug(
            "Processing attachment {}: {} bytes, {} chunks of {} bytes each",
            filename,
            file_size,
            total_chunks,
            chunk_size,
        )

        processed_bytes = 0
        chunk_counter = 0

        # Track file entry for central directory
        zip_filename = f"{base_path}/{filename}"
        local_header_offset = upload_context["current_offset"]

        # Calculate CRC-32 for the entire file first
        logger.debug("Calculating CRC-32 for attachment: {}", filename)
        crc32_value = calculate_file_crc32(
            storage_client, bucket_name, source_key, file_size, chunk_size
        )
        logger.debug("CRC-32 calculated for {}: {:08x}", filename, crc32_value)

        # Stream download in adaptive chunks and immediately upload to storage as zip parts
        for chunk_num, start_byte in enumerate(range(0, file_size, chunk_size)):
            end_byte = min(start_byte + chunk_size - 1, file_size - 1)
            chunk_length = end_byte - start_byte + 1

            # Download this chunk with retry logic
            chunk_data = download_chunk_with_retry(
                storage_client,
                bucket_name,
                source_key,
                ChunkDownloadConfig(start_byte=start_byte, end_byte=end_byte),
            )

            processed_bytes += chunk_length

            # Update progress
            new_progress = (chunk_num + 1) / total_chunks * 100
            metrics.current_attachment_progress = new_progress
            if progress_callback:
                progress_callback(metrics)

            # Create a zip part for this chunk and upload immediately
            # This prevents memory accumulation while maintaining zip structure
            zip_part_data = create_zip_part_for_chunk(
                chunk_data,
                zip_filename,
                chunk_num == 0,  # First chunk gets the file header
                chunk_num == total_chunks - 1,  # Last chunk gets the file footer
                file_size,
                crc32_value,  # Use the pre-calculated CRC-32 value
            )

            # Upload the zip part directly to storage with thread-safe coordination
            with upload_context["lock"]:
                part_number = upload_context["part_number"]
                part = storage_client.upload_part(
                    bucket_name, file_key, upload_id, part_number, zip_part_data
                )
                upload_context["parts"].append(part)
                upload_context["part_number"] = part_number + 1

                # Update offset for next file
                if chunk_num == 0:  # First chunk
                    upload_context["current_offset"] += len(zip_part_data)

        # Add file entry to central directory tracking with real CRC-32
        with upload_context["lock"]:
            upload_context["file_entries"].append(
                (
                    zip_filename,
                    file_size,
                    local_header_offset,
                    crc32_value,  # Use real CRC-32 instead of placeholder
                )
            )

        logger.debug(
            "Completed attachment {}: {} bytes in {} chunks with CRC-32: {:08x}",
            filename,
            file_size,
            total_chunks,
            crc32_value,
        )

        return {
            "processed_bytes": file_size,
            "chunks": total_chunks,
            "chunk_size": chunk_size,
        }

    except (
        StorageUploadError,
        OSError,
        ConnectionError,
        TimeoutError,
        ValueError,
        KeyError,
    ) as e:
        error_msg = f"Failed to process attachment {filename}: {e}"
        logger.error(error_msg)
        metrics.errors.append(error_msg)
        raise e
    finally:
        # Reset current attachment tracking
        metrics.current_attachment = None
        metrics.current_attachment_progress = 0.0


def create_zip_part_for_chunk(
    chunk_data: bytes,
    filename: str,
    is_first_chunk: bool,
    is_last_chunk: bool,
    file_size: int,
    crc32: int,
) -> bytes:
    """Create a zip part for a single chunk with proper ZIP structure.

    This function creates the minimal zip structure needed for a single chunk,
    including local file header and data descriptor if needed.

    Args:
        chunk_data: The binary data for this chunk
        filename: The filename to use in the ZIP structure
        is_first_chunk: Whether this is the first chunk (needs local file header)
        is_last_chunk: Whether this is the last chunk (needs data descriptor)
        file_size: The total size of the file
        crc32: The CRC-32 checksum for the entire file
    """
    # Create a minimal zip part buffer
    zip_part = BytesIO()

    if is_first_chunk:
        # Write local file header
        local_file_header = create_local_file_header(filename, file_size, crc32)
        zip_part.write(local_file_header)

    # Write the chunk data
    zip_part.write(chunk_data)

    if is_last_chunk:
        # Write data descriptor (for files > 4GB or when using ZIP64)
        data_descriptor = create_data_descriptor(file_size, crc32)
        zip_part.write(data_descriptor)

    zip_part.seek(0)
    return zip_part.getvalue()


def download_chunk_with_retry(
    storage_client: CloudStorageClient,
    bucket: str,
    key: str,
    config: ChunkDownloadConfig,
) -> bytes:
    """Download a chunk of data with retry logic."""
    for attempt in range(config.max_retries):
        try:
            return storage_client.get_object_range(
                bucket, key, config.start_byte, config.end_byte
            )
        except Exception as e:
            if attempt == config.max_retries - 1:
                raise
            logger.warning(
                "Chunk download attempt {} failed for {}/{} (bytes {}-{}): {}. Retrying...",
                attempt + 1,
                bucket,
                key,
                config.start_byte,
                config.end_byte,
                e,
            )
            time.sleep(0.1 * (2**attempt))  # Exponential backoff

    # This should never be reached due to the raise above, but mypy needs it
    raise RuntimeError("All retry attempts failed")


def calculate_file_crc32(
    storage_client: CloudStorageClient,
    bucket: str,
    key: str,
    file_size: int,
    chunk_size: int,
) -> int:
    """Calculate CRC-32 checksum for an entire file by processing it in chunks.

    This function downloads the file in chunks and calculates the CRC-32 checksum
    incrementally to avoid loading the entire file into memory at once.

    Args:
        storage_client: The storage client to use for downloads
        bucket: The bucket containing the file
        key: The key (path) of the file
        file_size: The total size of the file in bytes
        chunk_size: The size of each chunk to download

    Returns:
        The CRC-32 checksum as an integer
    """
    crc32_calculator = zlib.crc32(b"")

    for start_byte in range(0, file_size, chunk_size):
        end_byte = min(start_byte + chunk_size - 1, file_size - 1)
        chunk_length = end_byte - start_byte + 1

        # Download this chunk
        chunk_data = download_chunk_with_retry(
            storage_client,
            bucket,
            key,
            ChunkDownloadConfig(start_byte=start_byte, end_byte=end_byte),
        )

        # Update CRC-32 with this chunk's data
        crc32_calculator = zlib.crc32(chunk_data, crc32_calculator)

    return crc32_calculator


def upload_zip_part_to_storage(
    storage_client: CloudStorageClient,
    bucket_name: str,
    key: str,
    upload_id: str,
    part_number: int,
    zip_buffer: BytesIO,
) -> Any:
    """Upload a zip part to storage multipart upload."""

    # Validate buffer size
    buffer_size = zip_buffer.tell()
    if buffer_size == 0:
        raise ValueError("Cannot upload empty zip buffer")

    # Check if buffer size is reasonable (should not exceed 5GB for AWS S3)
    max_part_size = 5 * 1024 * 1024 * 1024  # 5GB
    if buffer_size > max_part_size:
        raise ValueError(
            f"Zip buffer size {buffer_size} bytes exceeds maximum part size {max_part_size} bytes"
        )

    # Get buffer content and upload
    buffer_content = zip_buffer.getvalue()
    response = storage_client.upload_part(
        bucket_name, key, upload_id, part_number, buffer_content
    )

    return response


def upload_to_storage_streaming(
    storage_client: CloudStorageClient,
    data: dict,
    config: StorageUploadConfig,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    progress_callback: Optional[ProgressCallback] = None,
    buffer_config: Optional[StreamingBufferConfig] = None,
) -> Tuple[Optional[AnyHttpUrlString], ProcessingMetrics]:
    """Uploads arbitrary data to cloud storage using true streaming without memory accumulation.

    This function processes data in small chunks and streams directly to storage,
    which is especially useful for large datasets with attachments.

    The true streaming approach includes:
    1. Direct download -> upload streaming (no memory accumulation)
    2. Parallel processing of multiple attachments
    3. Adaptive chunk sizes based on file size
    4. Progress tracking and comprehensive metrics
    5. Automatic package splitting for large datasets
    6. Robust error handling and retry logic
    7. Memory usage limited to individual chunk size (~1-5MB max)
    8. Cloud-agnostic storage operations
    """
    logger.info("Starting true streaming storage upload of {}", config.file_key)

    if privacy_request is None and document is not None:
        # Fall back to generic upload for document-only uploads
        # This would need to be implemented for the specific storage type
        raise NotImplementedError(
            "Document-only uploads not yet implemented for generic storage"
        )

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    metrics = None
    try:
        # Use true streaming approach with multipart upload
        if config.resp_format == ResponseFormat.csv.value:
            # For CSV with attachments, use the streaming zip approach
            # This handles both the CSV data and attachments in a streaming manner
            metrics = stream_attachments_to_storage_zip(
                storage_client,
                config.bucket_name,
                config.file_key,
                data,
                privacy_request,
                config.max_workers,
                progress_callback,
                buffer_config,
            )
        elif config.resp_format == ResponseFormat.json.value:
            # For JSON with attachments, use the streaming zip approach
            metrics = stream_attachments_to_storage_zip(
                storage_client,
                config.bucket_name,
                config.file_key,
                data,
                privacy_request,
                config.max_workers,
                progress_callback,
                buffer_config,
            )
        elif config.resp_format == ResponseFormat.html.value:

            metrics = stream_html_dsr_report_to_storage_multipart(
                storage_client,
                config.bucket_name,
                config.file_key,
                data,
                privacy_request,
            )
        else:
            raise NotImplementedError(
                f"No streaming support for format {config.resp_format}"
            )

        logger.info(
            "Successfully uploaded true streaming archive to storage: {}",
            config.file_key,
        )

    except (
        StorageUploadError,
        OSError,
        ConnectionError,
        TimeoutError,
        ValueError,
        NotImplementedError,
    ) as e:
        logger.error("Unexpected error during true streaming upload: {}", e)
        # Create empty metrics if upload failed
        if metrics is None:
            metrics = ProcessingMetrics()
        raise StorageUploadError(f"Unexpected error during true streaming upload: {e}")

    try:
        presigned_url: AnyHttpUrlString = storage_client.generate_presigned_url(
            config.bucket_name, config.file_key
        )

        return presigned_url, metrics

    except (StorageUploadError, OSError, ConnectionError, TimeoutError) as e:
        logger.error(
            "Encountered error while uploading and generating link for storage object: {}",
            e,
        )
        # Return metrics even if presigned URL generation failed
        return None, metrics
