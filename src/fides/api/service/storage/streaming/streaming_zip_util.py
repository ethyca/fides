import time
import zlib
from typing import List, Tuple


def create_local_file_header(filename: str, file_size: int, crc32: int) -> bytes:
    """Create a ZIP local file header for a file entry.

    Args:
        filename: The filename to include in the header
        file_size: The size of the file in bytes
        crc32: The CRC-32 checksum for the file
    """
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

    # CRC-32 (4 bytes) - use the provided CRC-32 value
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


def create_data_descriptor(file_size: int, crc32: int) -> bytes:
    """Create a ZIP data descriptor for file size information.

    Args:
        file_size: The size of the file in bytes
        crc32: The CRC-32 checksum for the file
    """
    # Data descriptor structure (16 bytes)
    descriptor = bytearray()

    # Data descriptor signature (4 bytes)
    descriptor.extend(b"PK\x07\x08")

    # CRC-32 (4 bytes) - use the provided CRC-32 value
    descriptor.extend(crc32.to_bytes(4, "little"))

    # Compressed size (4 bytes) - limit to 32-bit range
    compressed_size = min(file_size, 0xFFFFFFFF)
    descriptor.extend(compressed_size.to_bytes(4, "little"))

    # Uncompressed size (4 bytes) - limit to 32-bit range
    uncompressed_size = min(file_size, 0xFFFFFFFF)
    descriptor.extend(uncompressed_size.to_bytes(4, "little"))

    return bytes(descriptor)


def create_central_directory_header(
    filename: str, file_size: int, local_header_offset: int, crc32: int
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
