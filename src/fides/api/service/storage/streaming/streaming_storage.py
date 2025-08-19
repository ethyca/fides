from __future__ import annotations

import csv
import json
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

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
from fides.api.service.storage.streaming.util import (
    adaptive_chunk_size,
    should_split_package,
)
from fides.api.tasks.encryption_utils import encrypt_access_request_results
from fides.api.util.storage_util import StorageJSONEncoder
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def split_data_into_packages(
    data: dict, config: Optional[PackageSplitConfig] = None
) -> List[dict]:
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

    packages = []
    package_attachment_counts = []

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

    # Initialize metrics
    metrics = ProcessingMetrics()

    # Calculate total metrics upfront
    for value in data.values():
        if isinstance(value, list) and value:
            for item in value:
                attachments = item.get("attachments", [])
                metrics.total_attachments += len(attachments)
                metrics.total_bytes += sum(
                    att.get("size", 1024 * 1024) for att in attachments
                )

    logger.info(
        "Starting true streaming processing of {} attachments ({:.2f} GB total)",
        metrics.total_attachments,
        metrics.total_bytes / (1024**3),
    )

    # Check if we should split into multiple packages
    if should_split_package(data):
        logger.info("Large dataset detected, splitting into multiple packages")
        packages = split_data_into_packages(data)
        logger.info("Split into {} packages", len(packages))

        # Process each package separately
        all_metrics = []
        for i, package in enumerate(packages):
            package_key = f"{file_key}_part_{i+1}"
            logger.info(
                "Processing package {}/{}: {}", i + 1, len(packages), package_key
            )

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
        # Don't double-count attachments - use the original total from the main function
        combined_metrics.total_attachments = metrics.total_attachments
        combined_metrics.total_bytes = metrics.total_bytes
        for pm in all_metrics:
            combined_metrics.processed_attachments += pm.processed_attachments
            combined_metrics.processed_bytes += pm.processed_bytes
            combined_metrics.errors.extend(pm.errors)

        return combined_metrics

    # Initiate multipart upload for the zip file
    upload_id = None
    parts = []
    part_number = 1

    # Track file information for central directory
    file_entries = []  # List of (filename, size, offset, crc32) tuples
    current_offset = 0

    try:
        response = storage_client.create_multipart_upload(
            bucket_name, file_key, "application/zip"
        )
        upload_id = response.upload_id

        # Collect all attachments for parallel processing
        all_attachments = []
        for key, value in data.items():
            if isinstance(value, list) and value:
                for idx, item in enumerate(value):
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
        upload_context = {
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
                    attachment_info.attachment,
                    attachment_info.base_path,
                    metrics,
                    progress_callback,
                    buffer_config,
                ): attachment_info
                for attachment_info in all_attachments
            }

            # Process completed tasks
            for future in as_completed(future_to_attachment):
                attachment_info = future_to_attachment[future]
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
                        attachment_info.attachment.file_name or "unknown",
                    )

                except (
                    StorageUploadError,
                    OSError,
                    ConnectionError,
                    TimeoutError,
                ) as e:
                    error_msg = f"Failed to process attachment {attachment_info.attachment.file_name or 'unknown'}: {e}"
                    logger.error(error_msg)
                    metrics.errors.append(error_msg)

        # Update parts and part_number from context
        parts = upload_context["parts"]
        part_number = upload_context["part_number"]

        # Add the main item data (without attachments) as streaming zip parts
        for key, value in data.items():
            if isinstance(value, list) and value:
                for idx, item in enumerate(value):
                    # Only add item data if it's a non-empty dictionary with actual content
                    if item and isinstance(item, dict) and len(item) > 0:
                        try:
                            # Create CSV data in memory (small, acceptable)
                            csv_buffer = BytesIO()
                            csv_writer = csv.writer(csv_buffer)

                            # Write header - ensure keys are strings and handle any encoding issues
                            header = [str(k) for k in item.keys()]
                            csv_writer.writerow(header)
                            # Write data - ensure values are strings
                            row_data = [str(v) for v in item.values()]
                            csv_writer.writerow(row_data)

                            csv_buffer.seek(0)
                            csv_data = csv_buffer.getvalue()

                            # Create zip part for CSV data
                            filename = f"{key}/{idx + 1}/item.csv"
                            zip_part_data = create_zip_part_for_chunk(
                                csv_data,
                                filename,
                                True,  # First chunk
                                True,  # Last chunk
                                len(csv_data),
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
                                (filename, len(csv_data), current_offset, 0)
                            )
                            current_offset += len(zip_part_data)

                            part_number += 1

                        except (TypeError, UnicodeEncodeError, csv.Error) as e:
                            # If CSV writing failed, fall back to JSON
                            logger.warning(
                                f"CSV writing failed for item {key}/{idx + 1}, falling back to JSON: {e}"
                            )
                            try:
                                item_json = json.dumps(item, default=str)
                                json_data = item_json.encode("utf-8")

                                # Create zip part for JSON data
                                filename = f"{key}/{idx + 1}/item.json"
                                zip_part_data = create_zip_part_for_chunk(
                                    json_data,
                                    filename,
                                    True,  # First chunk
                                    True,  # Last chunk
                                    len(json_data),
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
                                file_entries.append(
                                    (filename, len(json_data), current_offset, 0)
                                )
                                current_offset += len(zip_part_data)

                                part_number += 1

                            except (
                                TypeError,
                                UnicodeEncodeError,
                                json.JSONEncodeError,
                            ) as json_error:
                                logger.error(
                                    f"Both CSV and JSON serialization failed for item {key}/{idx + 1}: CSV error: {e}, JSON error: {json_error}"
                                )
                                metrics.errors.append(
                                    f"Failed to serialize item {key}/{idx + 1}: {json_error}"
                                )
                                continue
                    elif item and not isinstance(item, dict):
                        # Fallback to JSON for non-dict items
                        try:
                            item_json = json.dumps(item, default=str)
                            json_data = item_json.encode("utf-8")

                            # Create zip part for JSON data
                            filename = f"{key}/{idx + 1}/item.json"
                            zip_part_data = create_zip_part_for_chunk(
                                json_data,
                                filename,
                                True,  # First chunk
                                True,  # Last chunk
                                len(json_data),
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
                            file_entries.append(
                                (filename, len(json_data), current_offset, 0)
                            )
                            current_offset += len(zip_part_data)

                            part_number += 1

                        except (
                            TypeError,
                            UnicodeEncodeError,
                            json.JSONEncodeError,
                        ) as e:
                            logger.error(
                                f"Failed to serialize non-dict item {key}/{idx + 1}: {e}"
                            )
                            metrics.errors.append(
                                f"Failed to serialize item {key}/{idx + 1}: {e}"
                            )
                            continue

        # Complete multipart upload only if we have parts
        if parts:
            # Create central directory
            central_dir_parts = create_central_directory_parts(
                file_entries, current_offset
            )

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
            storage_client.complete_multipart_upload(
                bucket_name, file_key, upload_id, []
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
) -> Dict[str, Any]:
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

        # Stream download in adaptive chunks and immediately upload to storage as zip parts
        for chunk_num, start_byte in enumerate(range(0, file_size, chunk_size)):
            end_byte = min(start_byte + chunk_size - 1, file_size - 1)
            chunk_length = end_byte - start_byte + 1

            # Download this chunk with retry logic
            chunk_data = download_chunk_with_retry(
                storage_client, bucket_name, source_key, start_byte, end_byte
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

        # Add file entry to central directory tracking
        with upload_context["lock"]:
            upload_context["file_entries"].append(
                (
                    zip_filename,
                    file_size,
                    local_header_offset,
                    0,  # CRC32 placeholder for now
                )
            )

        logger.debug(
            "Completed attachment {}: {} bytes in {} chunks",
            filename,
            file_size,
            total_chunks,
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
    crc32: int = 0,
) -> bytes:
    """Create a zip part for a single chunk with proper ZIP structure.

    This function creates the minimal zip structure needed for a single chunk,
    including local file header and data descriptor if needed.
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


def create_local_file_header(filename: str, file_size: int, crc32: int = 0) -> bytes:
    """Create a ZIP local file header for a file entry."""
    # ZIP local file header structure (30 bytes + filename length)
    header = bytearray()

    # Local file header signature (4 bytes)
    header.extend(b"PK\x03\x04")

    # Version needed to extract (2 bytes) - version 2.0
    header.extend(b"\x14\x00")

    # General purpose bit flag (2 bytes) - no encryption, normal compression
    header.extend(b"\x00\x00")

    # Compression method (2 bytes) - stored (no compression)
    header.extend(b"\x00\x00")

    # Last mod file time (2 bytes) - current time, but limit to 16-bit range
    current_time = int(time.time())
    # ZIP time format: hour*2048 + minute*32 + second/2
    # Limit to reasonable values to avoid overflow
    hour = min((current_time // 3600) % 24, 23)
    minute = min((current_time // 60) % 60, 59)
    second = min((current_time % 60), 59)
    zip_time = (hour << 11) | (minute << 5) | (second // 2)
    header.extend(zip_time.to_bytes(2, "little"))

    # Last mod file date (2 bytes) - current date, but limit to 16-bit range
    # ZIP date format: (year-1980)*512 + month*32 + day
    # Use a reasonable year to avoid overflow
    year = min(2024, 1980 + (current_time // (365 * 24 * 3600)))
    month = min(((current_time // (30 * 24 * 3600)) % 12) + 1, 12)
    day = min(((current_time // (24 * 3600)) % 30) + 1, 31)
    zip_date = ((year - 1980) << 9) | (month << 5) | day
    header.extend(zip_date.to_bytes(2, "little"))

    # CRC-32 (4 bytes) - use provided value or placeholder
    header.extend(crc32.to_bytes(4, "little"))

    # Compressed size (4 bytes) - limit to 32-bit range
    compressed_size = min(file_size, 0xFFFFFFFF)
    header.extend(compressed_size.to_bytes(4, "little"))

    # Uncompressed size (4 bytes) - limit to 32-bit range
    uncompressed_size = min(file_size, 0xFFFFFFFF)
    header.extend(uncompressed_size.to_bytes(4, "little"))

    # Filename length (2 bytes) - limit to 16-bit range
    filename_bytes = filename.encode("utf-8")
    filename_length = min(len(filename_bytes), 0xFFFF)
    header.extend(filename_length.to_bytes(2, "little"))

    # Extra field length (2 bytes) - none
    header.extend(b"\x00\x00")

    # Filename
    header.extend(filename_bytes)

    return bytes(header)


def create_data_descriptor(file_size: int, crc32: int = 0) -> bytes:
    """Create a ZIP data descriptor for file size information."""
    # Data descriptor structure (16 bytes)
    descriptor = bytearray()

    # Data descriptor signature (4 bytes)
    descriptor.extend(b"PK\x07\x08")

    # CRC-32 (4 bytes) - use provided value or placeholder
    descriptor.extend(crc32.to_bytes(4, "little"))

    # Compressed size (4 bytes) - limit to 32-bit range
    compressed_size = min(file_size, 0xFFFFFFFF)
    descriptor.extend(compressed_size.to_bytes(4, "little"))

    # Uncompressed size (4 bytes) - limit to 32-bit range
    uncompressed_size = min(file_size, 0xFFFFFFFF)
    descriptor.extend(uncompressed_size.to_bytes(4, "little"))

    return bytes(descriptor)


def create_central_directory_header(
    filename: str, file_size: int, local_header_offset: int, crc32: int = 0
) -> bytes:
    """Create a ZIP central directory header for a file entry."""
    # Central directory header structure (46 bytes + filename length)
    header = bytearray()

    # Central directory signature (4 bytes)
    header.extend(b"PK\x01\x02")

    # Version made by (2 bytes) - version 2.0
    header.extend(b"\x14\x00")

    # Version needed to extract (2 bytes) - version 2.0
    header.extend(b"\x14\x00")

    # General purpose bit flag (2 bytes) - same as local header
    if file_size > 0xFFFFFFFF:
        header.extend(b"\x08\x00")  # Data descriptor flag
    else:
        header.extend(b"\x00\x00")

    # Compression method (2 bytes) - stored (no compression)
    header.extend(b"\x00\x00")

    # Last mod file time (2 bytes) - current time, but limit to 16-bit range
    current_time = int(time.time())
    # ZIP time format: hour*2048 + minute*32 + second/2
    # Limit to reasonable values to avoid overflow
    hour = min((current_time // 3600) % 24, 23)
    minute = min((current_time // 60) % 60, 59)
    second = min((current_time % 60), 59)
    zip_time = (hour << 11) | (minute << 5) | (second // 2)
    header.extend(zip_time.to_bytes(2, "little"))

    # Last mod file date (2 bytes) - current date, but limit to 16-bit range
    # ZIP date format: (year-1980)*512 + month*32 + day
    # Use a reasonable year to avoid overflow
    year = min(2024, 1980 + (current_time // (365 * 24 * 3600)))
    month = min(((current_time // (30 * 24 * 3600)) % 12) + 1, 12)
    day = min(((current_time // (24 * 3600)) % 30) + 1, 31)
    zip_date = ((year - 1980) << 9) | (month << 5) | day
    header.extend(zip_date.to_bytes(2, "little"))

    # CRC-32 (4 bytes)
    header.extend(crc32.to_bytes(4, "little"))

    # Compressed size (4 bytes)
    if file_size > 0xFFFFFFFF:
        header.extend(b"\xff\xff\xff\xff")  # ZIP64 marker
    else:
        header.extend(file_size.to_bytes(4, "little"))

    # Uncompressed size (4 bytes)
    if file_size > 0xFFFFFFFF:
        header.extend(b"\xff\xff\xff\xff")  # ZIP64 marker
    else:
        header.extend(file_size.to_bytes(4, "little"))

    # Filename length (2 bytes)
    filename_bytes = filename.encode("utf-8")
    header.extend(len(filename_bytes).to_bytes(2, "little"))

    # Extra field length (2 bytes) - none for now
    header.extend(b"\x00\x00")

    # File comment length (2 bytes) - none
    header.extend(b"\x00\x00")

    # Disk number start (2 bytes) - 0
    header.extend(b"\x00\x00")

    # Internal file attributes (2 bytes) - 0
    header.extend(b"\x00\x00")

    # External file attributes (4 bytes) - 0
    header.extend(b"\x00\x00\x00\x00")

    # Relative offset of local header (4 bytes)
    if local_header_offset > 0xFFFFFFFF:
        header.extend(b"\xff\xff\xff\xff")  # ZIP64 marker
    else:
        # Ensure the offset fits in 4 bytes
        offset_bytes = (local_header_offset & 0xFFFFFFFF).to_bytes(4, "little")
        header.extend(offset_bytes)

    # Filename
    header.extend(filename_bytes)

    return bytes(header)


def create_central_directory_end(
    total_entries: int, central_dir_size: int, central_dir_offset: int
) -> bytes:
    """Create a ZIP end of central directory record."""
    # End of central directory structure (22 bytes)
    end_record = bytearray()

    # End of central directory signature (4 bytes)
    end_record.extend(b"PK\x05\x06")

    # Number of this disk (2 bytes) - 0
    end_record.extend(b"\x00\x00")

    # Number of the disk with the start of the central directory (2 bytes) - 0
    end_record.extend(b"\x00\x00")

    # Total number of entries in the central directory on this disk (2 bytes)
    if total_entries > 0xFFFF:
        end_record.extend(b"\xff\xff")  # ZIP64 marker
    else:
        end_record.extend(total_entries.to_bytes(2, "little"))

    # Total number of entries in the central directory (2 bytes)
    if total_entries > 0xFFFF:
        end_record.extend(b"\xff\xff")  # ZIP64 marker
    else:
        end_record.extend(total_entries.to_bytes(2, "little"))

    # Size of the central directory (4 bytes)
    if central_dir_size > 0xFFFFFFFF:
        end_record.extend(b"\xff\xff\xff\xff")  # ZIP64 marker
    else:
        end_record.extend(central_dir_size.to_bytes(4, "little"))

    # Offset of start of central directory with respect to the starting disk number (4 bytes)
    if central_dir_offset > 0xFFFFFFFF:
        end_record.extend(b"\xff\xff\xff\xff")  # ZIP64 marker
    else:
        # Ensure the offset fits in 4 bytes
        offset_bytes = (central_dir_offset & 0xFFFFFFFF).to_bytes(4, "little")
        end_record.extend(offset_bytes)

    # ZIP file comment length (2 bytes) - none
    end_record.extend(b"\x00\x00")

    return bytes(end_record)


def create_central_directory_parts(
    file_entries: List[Tuple[str, int, int, int]], data_end_offset: int
) -> List[bytes]:
    """Create central directory parts for a valid ZIP archive.

    Args:
        file_entries: List of (filename, size, offset, crc32) tuples
        data_end_offset: Offset where the central directory should start

    Returns:
        List of bytes objects representing central directory parts
    """
    if not file_entries:
        return []

    # Create central directory headers for each file
    central_dir_data = bytearray()

    for filename, file_size, local_header_offset, crc32 in file_entries:
        central_dir_header = create_central_directory_header(
            filename, file_size, local_header_offset, crc32
        )
        central_dir_data.extend(central_dir_header)

    # Create end of central directory record
    end_record = create_central_directory_end(
        len(file_entries), len(central_dir_data), data_end_offset
    )

    # Combine central directory and end record
    central_dir_data.extend(end_record)

    # Split into parts if too large (AWS S3 has 5GB part limit)
    max_part_size = 5 * 1024 * 1024 * 1024  # 5GB
    parts = []

    if len(central_dir_data) <= max_part_size:
        parts.append(bytes(central_dir_data))
    else:
        # Split into multiple parts if central directory is very large
        for i in range(0, len(central_dir_data), max_part_size):
            part_data = central_dir_data[i : i + max_part_size]
            parts.append(bytes(part_data))

    return parts


def download_chunk_with_retry(
    storage_client: CloudStorageClient,
    bucket_name: str,
    source_key: str,
    start_byte: int,
    end_byte: int,
    config: Optional[ChunkDownloadConfig] = None,
) -> bytes:
    """Download a chunk with automatic retry logic and exponential backoff."""

    # Use default config if none provided
    if config is None:
        config = ChunkDownloadConfig(start_byte=start_byte, end_byte=end_byte)

    for attempt in range(config.max_retries):
        try:
            chunk_data = storage_client.get_object_range(
                bucket_name, source_key, start_byte, end_byte
            )
            return chunk_data

        except (StorageUploadError, OSError, ConnectionError, TimeoutError) as e:
            if attempt == config.max_retries - 1:
                raise e

            wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
            logger.warning(
                "Chunk download failed (attempt {}/{}), retrying in {}s: {}",
                attempt + 1,
                config.max_retries,
                wait_time,
                e,
            )
            time.sleep(wait_time)

    raise Exception(f"Failed to download chunk after {config.max_retries} attempts")


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
