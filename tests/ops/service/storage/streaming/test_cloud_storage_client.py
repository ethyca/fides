"""Tests for the CloudStorageClient abstract base class."""

from typing import Any, Dict, List, Union, get_type_hints
from unittest.mock import create_autospec, patch

import pydantic_core
import pytest

from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.schemas import (
    MultipartUploadResponse,
    UploadPartResponse,
)


class TestCloudStorageClient:
    """Test cases for the CloudStorageClient abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that CloudStorageClient cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CloudStorageClient()

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = CloudStorageClient.__abstractmethods__
        expected_methods = {
            "create_multipart_upload",
            "upload_part",
            "complete_multipart_upload",
            "abort_multipart_upload",
            "put_object",
            "get_object",
            "generate_presigned_url",
        }
        assert abstract_methods == expected_methods

    def test_mock_implementation_works(self, mock_storage_client):
        """Test that our mock implementation can be instantiated."""
        assert isinstance(mock_storage_client, CloudStorageClient)

    def test_create_multipart_upload(self, mock_storage_client):
        """Test create_multipart_upload method."""
        response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
            metadata={"test": "value"},
        )

        assert isinstance(response, MultipartUploadResponse)
        assert response.upload_id.startswith("generic_upload_")
        assert response.metadata["bucket"] == "test-bucket"
        assert response.metadata["key"] == "test-key"
        assert response.metadata["content_type"] == "application/zip"

    def test_upload_part(self, mock_storage_client):
        """Test upload_part method."""
        # First create an upload
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        # Then upload a part
        part_response = mock_storage_client.upload_part(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"test data",
            metadata={"part": "metadata"},
        )

        assert isinstance(part_response, UploadPartResponse)
        assert part_response.etag.startswith("generic_etag_")
        assert part_response.part_number == 1
        assert part_response.metadata["part"] == "metadata"

    def test_upload_part_invalid_upload_id(self, mock_storage_client):
        """Test upload_part with invalid upload ID."""
        # Configure the mock to raise an error for invalid upload ID
        mock_storage_client.upload_part.side_effect = ValueError(
            "Upload invalid_id not found"
        )

        with pytest.raises(ValueError, match="Upload invalid_id not found"):
            mock_storage_client.upload_part(
                bucket="test-bucket",
                key="test-key",
                upload_id="invalid_id",
                part_number=1,
                body=b"test data",
            )

    def test_upload_part_bucket_key_mismatch(self, mock_storage_client):
        """Test upload_part with bucket/key mismatch."""
        # Configure the mock to raise an error for bucket/key mismatch
        mock_storage_client.upload_part.side_effect = ValueError("Bucket/key mismatch")

        with pytest.raises(ValueError, match="Bucket/key mismatch"):
            mock_storage_client.upload_part(
                bucket="wrong-bucket",
                key="wrong-key",
                upload_id="valid_id",
                part_number=1,
                body=b"test data",
            )

    def test_complete_multipart_upload(self, mock_storage_client):
        """Test complete_multipart_upload method."""
        # First create an upload
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        # Upload a few parts
        parts = []
        for i in range(3):
            part_response = mock_storage_client.upload_part(
                bucket="test-bucket",
                key="test-key",
                upload_id=upload_response.upload_id,
                part_number=i + 1,
                body=f"part {i + 1}".encode(),
            )
            parts.append(part_response)

        # Complete the upload
        mock_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=parts,
            metadata={"completion": "metadata"},
        )

        # Verify the method was called correctly
        mock_storage_client.complete_multipart_upload.assert_called_with(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=parts,
            metadata={"completion": "metadata"},
        )

    def test_complete_multipart_upload_no_metadata(self, mock_storage_client):
        """Test complete_multipart_upload without metadata."""
        # First create an upload
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        # Reset the side_effect to test the method call directly
        mock_storage_client.complete_multipart_upload.side_effect = None
        mock_storage_client.complete_multipart_upload.return_value = None

        # Complete the upload without metadata
        mock_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=[],
        )

        # Verify the method was called correctly
        # Note: When metadata is not explicitly passed, it won't be in the kwargs
        mock_storage_client.complete_multipart_upload.assert_called_with(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=[],
        )

    def test_abort_multipart_upload(self, mock_storage_client):
        """Test abort_multipart_upload method."""
        # First create an upload
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        # Abort the upload
        mock_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
        )

        # Verify the method was called correctly
        mock_storage_client.abort_multipart_upload.assert_called_with(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
        )

    def test_abort_multipart_upload_invalid_upload_id(self, mock_storage_client):
        """Test abort_multipart_upload with invalid upload ID."""
        # Configure the mock to raise an error for invalid upload ID
        mock_storage_client.abort_multipart_upload.side_effect = ValueError(
            "Upload invalid_id not found"
        )

        with pytest.raises(ValueError, match="Upload invalid_id not found"):
            mock_storage_client.abort_multipart_upload(
                bucket="test-bucket",
                key="test-key",
                upload_id="invalid_id",
            )

    def test_generate_presigned_url(self, mock_storage_client):
        """Test generate_presigned_url method."""
        # Reset the side_effect to use our custom return value
        mock_storage_client.generate_presigned_url.side_effect = None
        mock_storage_client.generate_presigned_url.return_value = (
            "https://test-bucket.s3.amazonaws.com/test-key?"
            "X-Amz-Algorithm=AWS4-HMAC-SHA256&"
            "X-Amz-Credential=test-credential&"
            "X-Amz-Date=20230101T000000Z&"
            "X-Amz-Expires=3600&"
            "X-Amz-SignedHeaders=host&"
            "X-Amz-Signature=test-signature"
        )

        response = mock_storage_client.generate_presigned_url(
            bucket="test-bucket",
            key="test-key",
        )

        assert isinstance(response, str)
        assert response.startswith("https://test-bucket.s3.amazonaws.com/test-key")
        assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in response

        # Verify the method was called correctly
        # Note: When ttl_seconds is not explicitly passed, it won't be in the kwargs
        mock_storage_client.generate_presigned_url.assert_called_with(
            bucket="test-bucket",
            key="test-key",
        )

    def test_generate_presigned_url_with_ttl(self, mock_storage_client):
        """Test generate_presigned_url method with TTL."""
        # Reset the side_effect to use our custom return value
        mock_storage_client.generate_presigned_url.side_effect = None
        mock_storage_client.generate_presigned_url.return_value = (
            "https://test-bucket.s3.amazonaws.com/test-key?"
            "X-Amz-Algorithm=AWS4-HMAC-SHA256&"
            "X-Amz-Credential=test-credential&"
            "X-Amz-Date=20230101T000000Z&"
            "X-Amz-Expires=7200&"  # 2 hours
            "X-Amz-SignedHeaders=host&"
            "X-Amz-Signature=test-signature"
        )

        response = mock_storage_client.generate_presigned_url(
            bucket="test-bucket",
            key="test-key",
            ttl_seconds=7200,  # 2 hours
        )

        assert isinstance(response, str)
        assert "X-Amz-Expires=7200" in response

        # Verify the method was called correctly
        mock_storage_client.generate_presigned_url.assert_called_with(
            bucket="test-bucket",
            key="test-key",
            ttl_seconds=7200,
        )

    def test_generate_presigned_url_generation_failed(self, mock_storage_client):
        """Test generate_presigned_url when URL generation fails."""
        # Reset the side_effect and set a custom error
        mock_storage_client.generate_presigned_url.side_effect = None
        mock_storage_client.generate_presigned_url.side_effect = Exception(
            "Failed to generate presigned URL"
        )

        with pytest.raises(Exception, match="Failed to generate presigned URL"):
            mock_storage_client.generate_presigned_url(
                bucket="test-bucket",
                key="test-key",
            )

    def test_abstract_method_signatures(self):
        """Test that abstract methods have correct signatures."""
        # Get method signatures
        create_multipart_upload_sig = get_type_hints(
            CloudStorageClient.create_multipart_upload
        )
        upload_part_sig = get_type_hints(CloudStorageClient.upload_part)
        complete_multipart_upload_sig = get_type_hints(
            CloudStorageClient.complete_multipart_upload
        )
        abort_multipart_upload_sig = get_type_hints(
            CloudStorageClient.abort_multipart_upload
        )
        generate_presigned_url_sig = get_type_hints(
            CloudStorageClient.generate_presigned_url
        )

        # Verify return types
        assert create_multipart_upload_sig["return"] == MultipartUploadResponse
        assert upload_part_sig["return"] == UploadPartResponse
        assert complete_multipart_upload_sig["return"] == type(None)
        assert abort_multipart_upload_sig["return"] == type(None)
        assert generate_presigned_url_sig["return"] == pydantic_core.Url

        # Verify parameter types
        assert create_multipart_upload_sig["bucket"] == str
        assert create_multipart_upload_sig["key"] == str
        assert create_multipart_upload_sig["content_type"] == str

        # Check metadata parameter type more flexibly
        metadata_type = create_multipart_upload_sig["metadata"]
        assert metadata_type is not None
        # Should be Optional[Dict[str, str]] or Optional[dict[str, str]]
        if hasattr(metadata_type, "__origin__") and metadata_type.__origin__ is Union:
            # It's an Optional type
            args = metadata_type.__args__
            assert len(args) == 2
            assert args[1] == type(None)  # None type
            dict_type = args[0]
            assert dict_type in [Dict[str, str], dict[str, str]]
        else:
            # Fallback check
            assert "Optional" in str(metadata_type) or "Union" in str(metadata_type)

        assert upload_part_sig["bucket"] == str
        assert upload_part_sig["key"] == str
        assert upload_part_sig["upload_id"] == str
        assert upload_part_sig["part_number"] == int
        assert upload_part_sig["body"] == bytes

        # Check upload_part metadata parameter type
        upload_metadata_type = upload_part_sig["metadata"]
        assert upload_metadata_type is not None
        if (
            hasattr(upload_metadata_type, "__origin__")
            and upload_metadata_type.__origin__ is Union
        ):
            args = upload_metadata_type.__args__
            assert len(args) == 2
            assert args[1] == type(None)
            dict_type = args[0]
            assert dict_type in [Dict[str, str], dict[str, str]]
        else:
            assert "Optional" in str(upload_metadata_type) or "Union" in str(
                upload_metadata_type
            )

        assert complete_multipart_upload_sig["bucket"] == str
        assert complete_multipart_upload_sig["key"] == str
        assert complete_multipart_upload_sig["upload_id"] == str

        # Check parts parameter type flexibly
        parts_type = complete_multipart_upload_sig["parts"]
        assert parts_type is not None
        # Should be List[UploadPartResponse] or list[UploadPartResponse]
        if hasattr(parts_type, "__origin__"):
            assert parts_type.__origin__ in [List, list]
            args = parts_type.__args__
            assert len(args) == 1
            assert args[0] == UploadPartResponse
        else:
            # Fallback check
            assert "List" in str(parts_type) or "list" in str(parts_type)

        # Check complete_multipart_upload metadata parameter type
        complete_metadata_type = complete_multipart_upload_sig["metadata"]
        assert complete_metadata_type is not None
        if (
            hasattr(complete_metadata_type, "__origin__")
            and complete_metadata_type.__origin__ is Union
        ):
            args = complete_metadata_type.__args__
            assert len(args) == 2
            assert args[1] == type(None)
            dict_type = args[0]
            assert dict_type in [Dict[str, str], dict[str, str]]
        else:
            assert "Optional" in str(complete_metadata_type) or "Union" in str(
                complete_metadata_type
            )

        assert abort_multipart_upload_sig["bucket"] == str
        assert abort_multipart_upload_sig["key"] == str
        assert abort_multipart_upload_sig["upload_id"] == str

        assert generate_presigned_url_sig["bucket"] == str
        assert generate_presigned_url_sig["key"] == str

        # Check ttl_seconds parameter type
        ttl_type = generate_presigned_url_sig["ttl_seconds"]
        assert ttl_type is not None
        if hasattr(ttl_type, "__origin__") and ttl_type.__origin__ is Union:
            args = ttl_type.__args__
            assert len(args) == 2
            assert args[1] == type(None)
            assert args[0] == int
        else:
            assert "Optional" in str(ttl_type) or "Union" in str(ttl_type)
