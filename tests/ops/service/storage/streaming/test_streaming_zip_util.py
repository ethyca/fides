from fides.api.service.storage.streaming.streaming_zip_util import (
    create_central_directory_end,
    create_central_directory_header,
    create_central_directory_parts,
    create_data_descriptor,
    create_local_file_header,
)


class TestStreamingZipUtil:
    def test_create_local_file_header(self):
        """Test ZIP local file header creation."""
        filename = "test.txt"
        file_size = 1024
        crc32 = 0x12345678  # Test CRC-32 value

        header = create_local_file_header(filename, file_size, crc32)

        # Check ZIP signature
        assert header[:4] == b"PK\x03\x04"

        # Check filename length (2 bytes at position 26-27)
        filename_length = int.from_bytes(header[26:28], "little")
        assert filename_length == len(filename)

        # Check file size (4 bytes at position 18-21)
        size_from_header = int.from_bytes(header[18:22], "little")
        assert size_from_header == file_size

        # Check CRC-32 (4 bytes at position 14-17)
        crc32_from_header = int.from_bytes(header[14:18], "little")
        assert crc32_from_header == crc32

        # Check filename is present
        assert filename.encode("utf-8") in header

    def test_create_local_file_header_with_unicode_filename(self):
        """Test ZIP local file header creation with Unicode filename."""
        filename = "test_文件.txt"
        file_size = 512
        crc32 = 0xABCDEF01

        header = create_local_file_header(filename, file_size, crc32)

        # Check ZIP signature
        assert header[:4] == b"PK\x03\x04"

        # Check filename length matches UTF-8 encoded length
        filename_bytes = filename.encode("utf-8")
        filename_length = int.from_bytes(header[26:28], "little")
        assert filename_length == len(filename_bytes)

        # Check filename is present
        assert filename_bytes in header

    def test_create_local_file_header_large_file_size(self):
        """Test ZIP local file header creation with large file size."""
        filename = "large_file.bin"
        file_size = 0xFFFFFFFF  # Max 32-bit value
        crc32 = 0x12345678

        header = create_local_file_header(filename, file_size, crc32)

        # Check file size is properly truncated
        size_from_header = int.from_bytes(header[18:22], "little")
        assert size_from_header == 0xFFFFFFFF

    def test_create_local_file_header_very_large_file_size(self):
        """Test ZIP local file header creation with very large file size."""
        filename = "very_large_file.bin"
        file_size = 0x1FFFFFFFF  # Larger than 32-bit
        crc32 = 0x12345678

        header = create_local_file_header(filename, file_size, crc32)

        # Check file size is properly truncated to 32-bit max
        size_from_header = int.from_bytes(header[18:22], "little")
        assert size_from_header == 0xFFFFFFFF

    def test_create_data_descriptor(self):
        """Test ZIP data descriptor creation."""
        file_size = 2048
        crc32 = 0x87654321  # Test CRC-32 value

        descriptor = create_data_descriptor(file_size, crc32)

        # Check data descriptor signature
        assert descriptor[:4] == b"PK\x07\x08"

        # Check CRC-32 (4 bytes at position 4-7)
        crc32_from_descriptor = int.from_bytes(descriptor[4:8], "little")
        assert crc32_from_descriptor == crc32

        # Check file size (4 bytes at position 8-11)
        size_from_descriptor = int.from_bytes(descriptor[8:12], "little")
        assert size_from_descriptor == file_size

    def test_create_data_descriptor_large_file_size(self):
        """Test ZIP data descriptor creation with large file size."""
        file_size = 0xFFFFFFFF  # Max 32-bit value
        crc32 = 0x87654321

        descriptor = create_data_descriptor(file_size, crc32)

        # Check file size is properly truncated
        size_from_descriptor = int.from_bytes(descriptor[8:12], "little")
        assert size_from_descriptor == 0xFFFFFFFF

    def test_create_data_descriptor_very_large_file_size(self):
        """Test ZIP data descriptor creation with very large file size."""
        file_size = 0x1FFFFFFFF  # Larger than 32-bit
        crc32 = 0x87654321

        descriptor = create_data_descriptor(file_size, crc32)

        # Check file size is properly truncated to 32-bit max
        size_from_descriptor = int.from_bytes(descriptor[8:12], "little")
        assert size_from_descriptor == 0xFFFFFFFF

    def test_create_central_directory_header(self):
        """Test ZIP central directory header creation."""
        filename = "test.txt"
        file_size = 1024
        local_header_offset = 0
        crc32 = 0x12345678

        header = create_central_directory_header(
            filename, file_size, local_header_offset, crc32
        )

        # Check central directory signature
        assert header[:4] == b"PK\x01\x02"

        # Check filename length
        filename_bytes = filename.encode("utf-8")
        filename_length = int.from_bytes(header[28:30], "little")
        assert filename_length == len(filename_bytes)

        # Check CRC-32
        crc32_from_header = int.from_bytes(header[16:20], "little")
        assert crc32_from_header == crc32

        # Check file size
        size_from_header = int.from_bytes(header[20:24], "little")
        assert size_from_header == file_size

        # Check local header offset
        offset_from_header = int.from_bytes(header[42:46], "little")
        assert offset_from_header == local_header_offset

        # Check filename is present
        assert filename_bytes in header

    def test_create_central_directory_header_large_file_size(self):
        """Test ZIP central directory header creation with large file size."""
        filename = "large_file.bin"
        file_size = 0xFFFFFFFF  # Max 32-bit value
        local_header_offset = 1000
        crc32 = 0x12345678

        header = create_central_directory_header(
            filename, file_size, local_header_offset, crc32
        )

        # Check general purpose bit flag (should NOT indicate data descriptor for exactly 4GB)
        general_purpose_flag = int.from_bytes(header[8:10], "little")
        assert general_purpose_flag == 0x0000  # No data descriptor flag for exactly 4GB

        # Check file size (should be 0xFFFFFFFF)
        size_from_header = int.from_bytes(header[20:24], "little")
        assert size_from_header == 0xFFFFFFFF

    def test_create_central_directory_header_very_large_file_size(self):
        """Test ZIP central directory header creation with very large file size."""
        filename = "very_large_file.bin"
        file_size = 0x1FFFFFFFF  # Larger than 32-bit
        local_header_offset = 2000
        crc32 = 0x12345678

        header = create_central_directory_header(
            filename, file_size, local_header_offset, crc32
        )

        # Check general purpose bit flag (should indicate data descriptor)
        general_purpose_flag = int.from_bytes(header[8:10], "little")
        assert general_purpose_flag == 0x0008  # Data descriptor flag

        # Check file size (should be 0xFFFFFFFF for ZIP64)
        size_from_header = int.from_bytes(header[20:24], "little")
        assert size_from_header == 0xFFFFFFFF

    def test_create_central_directory_header_large_offset(self):
        """Test ZIP central directory header creation with large local header offset."""
        filename = "test.txt"
        file_size = 1024
        local_header_offset = 0xFFFFFFFF  # Max 32-bit offset
        crc32 = 0x12345678

        header = create_central_directory_header(
            filename, file_size, local_header_offset, crc32
        )

        # Check local header offset (should be 0xFFFFFFFF for ZIP64)
        offset_from_header = int.from_bytes(header[42:46], "little")
        assert offset_from_header == 0xFFFFFFFF

    def test_create_central_directory_header_very_large_offset(self):
        """Test ZIP central directory header creation with very large local header offset."""
        filename = "test.txt"
        file_size = 1024
        local_header_offset = 0x1FFFFFFFF  # Larger than 32-bit
        crc32 = 0x12345678

        header = create_central_directory_header(
            filename, file_size, local_header_offset, crc32
        )

        # Check local header offset (should be 0xFFFFFFFF for ZIP64)
        offset_from_header = int.from_bytes(header[42:46], "little")
        assert offset_from_header == 0xFFFFFFFF

    def test_create_central_directory_end(self):
        """Test ZIP end of central directory record creation."""
        total_entries = 5
        central_dir_size = 1024
        central_dir_offset = 500

        end_record = create_central_directory_end(
            total_entries, central_dir_size, central_dir_offset
        )

        # Check end of central directory signature
        assert end_record[:4] == b"PK\x05\x06"

        # Check total entries
        entries_from_record = int.from_bytes(end_record[10:12], "little")
        assert entries_from_record == total_entries

        # Check central directory size
        size_from_record = int.from_bytes(end_record[12:16], "little")
        assert size_from_record == central_dir_size

        # Check central directory offset
        offset_from_record = int.from_bytes(end_record[16:20], "little")
        assert offset_from_record == central_dir_offset

    def test_create_central_directory_end_large_values(self):
        """Test ZIP end of central directory record creation with large values."""
        total_entries = 0xFFFF  # Max 16-bit value
        central_dir_size = 0xFFFFFFFF  # Max 32-bit value
        central_dir_offset = 0xFFFFFFFF  # Max 32-bit value

        end_record = create_central_directory_end(
            total_entries, central_dir_size, central_dir_offset
        )

        # Check total entries
        entries_from_record = int.from_bytes(end_record[10:12], "little")
        assert entries_from_record == 0xFFFF

        # Check central directory size
        size_from_record = int.from_bytes(end_record[12:16], "little")
        assert size_from_record == 0xFFFFFFFF

        # Check central directory offset
        offset_from_record = int.from_bytes(end_record[16:20], "little")
        assert offset_from_record == 0xFFFFFFFF

    def test_create_central_directory_end_very_large_values(self):
        """Test ZIP end of central directory record creation with very large values."""
        total_entries = 0x1FFFF  # Larger than 16-bit
        central_dir_size = 0x1FFFFFFFF  # Larger than 32-bit
        central_dir_offset = 0x1FFFFFFFF  # Larger than 32-bit

        end_record = create_central_directory_end(
            total_entries, central_dir_size, central_dir_offset
        )

        # Check total entries (should be 0xFFFF for ZIP64)
        entries_from_record = int.from_bytes(end_record[10:12], "little")
        assert entries_from_record == 0xFFFF

        # Check central directory size (should be 0xFFFFFFFF for ZIP64)
        size_from_record = int.from_bytes(end_record[12:16], "little")
        assert size_from_record == 0xFFFFFFFF

        # Check central directory offset (should be 0xFFFFFFFF for ZIP64)
        offset_from_record = int.from_bytes(end_record[16:20], "little")
        assert offset_from_record == 0xFFFFFFFF

    def test_create_central_directory_parts_empty_list(self):
        """Test central directory parts creation with empty file entries."""
        file_entries = []
        data_end_offset = 0

        parts = create_central_directory_parts(file_entries, data_end_offset)

        assert parts == []

    def test_create_central_directory_parts_single_file(self):
        """Test central directory parts creation with single file."""
        file_entries = [("test.txt", 1024, 0, 0x12345678)]
        data_end_offset = 100

        parts = create_central_directory_parts(file_entries, data_end_offset)

        assert len(parts) == 1
        central_dir_data = parts[0]

        # Check that central directory header is present
        assert b"PK\x01\x02" in central_dir_data

        # Check that end record is present
        assert b"PK\x05\x06" in central_dir_data

        # Check filename is present
        assert b"test.txt" in central_dir_data

    def test_create_central_directory_parts_multiple_files(self):
        """Test central directory parts creation with multiple files."""
        file_entries = [
            ("file1.txt", 1024, 0, 0x12345678),
            ("file2.txt", 2048, 200, 0x87654321),
            ("file3.txt", 512, 500, 0xABCDEF01),
        ]
        data_end_offset = 1000

        parts = create_central_directory_parts(file_entries, data_end_offset)

        assert len(parts) == 1
        central_dir_data = parts[0]

        # Check that central directory headers are present
        assert b"PK\x01\x02" in central_dir_data

        # Check that end record is present
        assert b"PK\x05\x06" in central_dir_data

        # Check all filenames are present
        assert b"file1.txt" in central_dir_data
        assert b"file2.txt" in central_dir_data
        assert b"file3.txt" in central_dir_data

    def test_create_central_directory_parts_large_directory(self):
        """Test central directory parts creation with large directory."""
        # Create many file entries to test large directory handling
        file_entries = []
        for i in range(1000):
            filename = f"file_{i:04d}.txt"
            file_size = 1024 + i
            offset = i * 100
            crc32 = 0x12345678 + i
            file_entries.append((filename, file_size, offset, crc32))

        data_end_offset = 100000

        parts = create_central_directory_parts(file_entries, data_end_offset)

        # Should still be one part since it's under 5GB limit
        assert len(parts) == 1

        central_dir_data = parts[0]

        # Check that central directory headers are present
        assert b"PK\x01\x02" in central_dir_data

        # Check that end record is present
        assert b"PK\x05\x06" in central_dir_data

        # Check some filenames are present
        assert b"file_0000.txt" in central_dir_data
        assert b"file_0999.txt" in central_dir_data

    def test_create_central_directory_parts_with_large_files(self):
        """Test central directory parts creation with large files."""
        file_entries = [
            ("large_file1.bin", 0xFFFFFFFF, 0, 0x12345678),
            ("large_file2.bin", 0x1FFFFFFFF, 1000, 0x87654321),
        ]
        data_end_offset = 2000

        parts = create_central_directory_parts(file_entries, data_end_offset)

        assert len(parts) == 1
        central_dir_data = parts[0]

        # Check that central directory headers are present
        assert b"PK\x01\x02" in central_dir_data

        # Check that end record is present
        assert b"PK\x05\x06" in central_dir_data

        # Check filenames are present
        assert b"large_file1.bin" in central_dir_data
        assert b"large_file2.bin" in central_dir_data

    def test_time_and_date_handling_edge_cases(self):
        """Test time and date handling in headers with edge cases."""
        # Test with very large timestamp values
        filename = "edge_case.txt"
        file_size = 1024
        crc32 = 0x12345678

        header = create_local_file_header(filename, file_size, crc32)

        # Check that time and date fields are within valid ranges
        time_field = int.from_bytes(header[10:12], "little")
        date_field = int.from_bytes(header[12:14], "little")

        # Time should be reasonable (hour*2048 + minute*32 + second/2)
        assert 0 <= time_field <= 0xFFFF

        # Date should be reasonable ((year-1980)*512 + month*32 + day)
        assert 0 <= date_field <= 0xFFFF

    def test_filename_encoding_edge_cases(self):
        """Test filename encoding edge cases."""
        # Test with very long filename
        long_filename = "a" * 1000
        file_size = 1024
        crc32 = 0x12345678

        header = create_local_file_header(long_filename, file_size, crc32)

        # Check filename length is properly truncated to 16-bit max
        filename_length = int.from_bytes(header[26:28], "little")
        assert filename_length <= 0xFFFF

        # Test with empty filename
        empty_filename = ""
        header = create_local_file_header(empty_filename, file_size, crc32)

        # Check filename length is 0
        filename_length = int.from_bytes(header[26:28], "little")
        assert filename_length == 0

    def test_crc32_edge_cases(self):
        """Test CRC-32 handling edge cases."""
        filename = "test.txt"
        file_size = 1024

        # Test with 0 CRC
        crc32 = 0
        header = create_local_file_header(filename, file_size, crc32)
        crc32_from_header = int.from_bytes(header[14:18], "little")
        assert crc32_from_header == 0

        # Test with max CRC
        crc32 = 0xFFFFFFFF
        header = create_local_file_header(filename, file_size, crc32)
        crc32_from_header = int.from_bytes(header[14:18], "little")
        assert crc32_from_header == 0xFFFFFFFF

    def test_create_central_directory_header(self):
        """Test ZIP central directory header creation."""
        filename = "test.txt"
        file_size = 1024
        local_header_offset = 0
        crc32 = 0xDEADBEEF  # Test CRC-32 value

        header = create_central_directory_header(
            filename, file_size, local_header_offset, crc32
        )

        # Check ZIP central directory signature
        assert header[:4] == b"PK\x01\x02"

        # Check filename length (2 bytes at position 28-29)
        filename_length = int.from_bytes(header[28:30], "little")
        assert filename_length == len(filename)

        # Check file size (4 bytes at position 20-23)
        size_from_header = int.from_bytes(header[20:24], "little")
        assert size_from_header == file_size

        # Check CRC-32 (4 bytes at position 16-19)
        crc32_from_header = int.from_bytes(header[16:20], "little")
        assert crc32_from_header == crc32

        # Check filename is present
        assert filename.encode("utf-8") in header

    def test_create_central_directory_end(self):
        """Test ZIP end of central directory record creation."""

        total_entries = 5
        central_dir_size = 1024
        central_dir_offset = 2048

        end_record = create_central_directory_end(
            total_entries, central_dir_size, central_dir_offset
        )

        # Check ZIP end of central directory signature
        assert end_record[:4] == b"PK\x05\x06"

        # Check total entries (2 bytes at position 8-9)
        entries_from_record = int.from_bytes(end_record[8:10], "little")
        assert entries_from_record == total_entries

        # Check central directory size (4 bytes at position 12-15)
        size_from_record = int.from_bytes(end_record[12:16], "little")
        assert size_from_record == central_dir_size

        # Check central directory offset (4 bytes at position 16-19)
        offset_from_record = int.from_bytes(end_record[16:20], "little")
        assert offset_from_record == central_dir_offset

    def test_create_central_directory_parts(self):
        """Test central directory parts creation."""
        # Test with empty file entries
        empty_parts = create_central_directory_parts([], 0)
        assert empty_parts == []

        # Test with single file entry
        file_entries = [("test.txt", 1024, 0, 0)]
        parts = create_central_directory_parts(file_entries, 2048)

        assert len(parts) == 1
        central_dir_part = parts[0]

        # Should contain central directory header and end record
        assert b"PK\x01\x02" in central_dir_part  # Central directory header
        assert b"PK\x05\x06" in central_dir_part  # End of central directory

    def test_zip64_support(self):
        """Test ZIP64 support for large files."""

        # Test with file size > 4GB
        large_file_size = 5 * 1024 * 1024 * 1024  # 5GB
        crc32 = 0xCAFEBABE  # Test CRC-32 value

        # Local file header should use ZIP64 markers
        header = create_local_file_header("large_file.txt", large_file_size, crc32)

        # Check that ZIP64 markers are used for sizes > 4GB
        compressed_size = int.from_bytes(header[18:22], "little")
        uncompressed_size = int.from_bytes(header[22:26], "little")

        # Should be 0xFFFFFFFF for ZIP64
        assert compressed_size == 0xFFFFFFFF
        assert uncompressed_size == 0xFFFFFFFF

        # Data descriptor should handle large sizes
        descriptor = create_data_descriptor(large_file_size, crc32)
        assert descriptor[:4] == b"PK\x07\x08"  # Data descriptor signature
