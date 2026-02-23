import types
from unittest.mock import create_autospec

import google.auth.credentials
import pytest
import requests
from google.api_core.exceptions import NotFound
from google.cloud import storage

from fides.api.schemas.storage.storage import StorageDetails


@pytest.fixture
def base_gcs_client_mock():
    """Fixture to provide a base mock for Google Cloud Storage (GCS) client.

    This fixture creates a base mock of the GCS client with proper method signatures
    and basic functionality. It uses `create_autospec` to ensure that the mock
    maintains the same interface as the real GCS client, which helps catch interface
    changes and ensures type safety.

    The fixture sets up:
    - Mock credentials with proper autospec
    - Mock client with required attributes
    - Mock batch stack for handling batch operations
    - Mock HTTP transport for handling requests
    - Basic bucket method implementation

    Usage:
        ```python
        def test_something(base_gcs_client_mock):
            # The mock client will have the same interface as the real GCS client
            bucket = base_gcs_client_mock.bucket("my-bucket")
            # Any method calls will be properly type-checked
        ```

    Why autospec is used:
    - Ensures the mock has the same interface as the real GCS client
    - Catches interface changes that would break the real code
    - Provides better error messages when methods are called incorrectly
    - Maintains type safety throughout the test
    """
    # Create mock credentials with proper autospec
    mock_credentials = create_autospec(google.auth.credentials.Credentials)
    mock_credentials.valid = True
    mock_credentials.expired = False
    mock_credentials.refresh = create_autospec(
        google.auth.credentials.Credentials.refresh, side_effect=lambda: None
    )

    # Create mock client with proper autospec
    mock_client = create_autospec(storage.Client)
    mock_client._credentials = mock_credentials
    mock_client.project = "test-project"

    # Set up batch stack
    class MockBatchStack:
        """Mock implementation of GCS batch operation stack."""

        def __init__(self):
            self._stack = []

        @property
        def top(self):
            """Returns the top batch in the stack or None if empty."""
            return self._stack[-1] if self._stack else None

        def push(self, batch):
            """Adds a new batch to the top of the stack."""
            self._stack.append(batch)

        def pop(self):
            """Removes and returns the top batch from the stack."""
            return self._stack.pop() if self._stack else None

    # Set up HTTP transport with proper autospec
    mock_http = create_autospec(requests.Session)
    mock_response = create_autospec(requests.Response)
    mock_response.status_code = 200
    mock_http.request = create_autospec(
        requests.Session.request, return_value=mock_response
    )

    # Add required attributes to mock client
    mock_client._batch_stack = MockBatchStack()
    mock_client._http_internal = mock_http
    mock_client._http = mock_http

    # Set up bucket method with proper autospec
    def mock_get_bucket(self, bucket_name, user_project=None, generation=None):
        """Creates and returns a mock bucket with the given name."""
        mock_bucket = create_autospec(storage.Bucket)
        mock_bucket.name = bucket_name
        return mock_bucket

    mock_client.bucket = types.MethodType(
        create_autospec(storage.Client.bucket, side_effect=mock_get_bucket), mock_client
    )

    return mock_client


@pytest.fixture(scope="function")
def mock_gcs_client(
    base_gcs_client_mock, monkeypatch, storage_config_default_gcs, attachment_file
):
    """Fixture to provide a fully configured mock GCS client for attachment testing.

    This fixture extends the base_gcs_client_mock with attachment-specific behavior,
    implementing a mock of the GCS client's functionality needed for testing
    upload and deletion of files. It uses `create_autospec` to ensure type safety and proper
    method signatures throughout the mock hierarchy.

    Key features:
    - Tracks all blobs in a bucket using a dictionary
    - Simulates blob creation, deletion, and access
    - Implements proper error handling (e.g., NotFound exceptions)
    - Supports blob listing with prefix filtering
    - Maintains proper method signatures through autospec

    The mock implements the following GCS operations:
    - Blob creation and upload
    - Blob deletion
    - Blob retrieval
    - Signed URL generation
    - Blob listing with prefix support

    Usage:
        ```python
        def test_attachment_operations(mock_gcs_client):
            # Create and upload an attachment
            bucket = mock_gcs_client.bucket("test-bucket")
            blob = bucket.blob("test-file.txt")
            blob.upload_from_file(file_obj)

            # Delete the attachment
            blob.delete()

            # Attempting to access deleted blob raises NotFound
            with pytest.raises(NotFound):
                blob.reload()
        ```

    Why autospec is used:
    - Ensures all mock methods have the same signature as real GCS methods
    - Catches interface changes that would break the real code
    - Provides better error messages for incorrect method calls
    - Maintains type safety throughout the test
    - Helps catch bugs related to method signature changes

    Dependencies:
        - base_gcs_client_mock: Provides the base GCS client mock
        - storage_config_default_gcs: Provides GCS storage configuration
        - attachment_file: Provides test file content for size calculations
    """
    # Get the file content for size calculation
    file_content = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset file pointer

    # Create a mock bucket with proper autospec
    mock_bucket = create_autospec(storage.Bucket)
    mock_bucket.name = storage_config_default_gcs.details[StorageDetails.BUCKET.value]

    # Track all blobs
    blobs = {}

    # Set up the mock bucket's blob method with proper autospec
    def mock_get_blob(self, blob_name, *args, **kwargs):
        """Retrieves a blob by name, raising NotFound if it doesn't exist."""
        # Check if blob exists
        if blob_name not in blobs:
            raise NotFound(f"Blob {blob_name} not found")

        mock_blob = blobs[blob_name]
        return mock_blob

    # Set up bucket methods with proper autospec
    mock_bucket.blob = types.MethodType(
        create_autospec(storage.Bucket.blob, side_effect=mock_get_blob), mock_bucket
    )

    def mock_list_blobs(
        self, prefix=None, delimiter=None, max_results=None, page_token=None, **kwargs
    ):
        """Lists all blobs in the bucket, optionally filtered by prefix."""
        if prefix:
            return [blob for name, blob in blobs.items() if name.startswith(prefix)]
        return list(blobs.values())

    mock_bucket.list_blobs = types.MethodType(
        create_autospec(storage.Bucket.list_blobs, side_effect=mock_list_blobs),
        mock_bucket,
    )

    # Set up the mock client's bucket method with proper autospec
    def mock_get_bucket(self, bucket_name, user_project=None, generation=None):
        """Returns the mock bucket if the name matches, otherwise raises ValueError."""
        if bucket_name != mock_bucket.name:
            raise ValueError(
                f"Expected bucket name {mock_bucket.name}, got {bucket_name}"
            )
        return mock_bucket

    # Update the base mock's bucket method with proper autospec
    base_gcs_client_mock.bucket = types.MethodType(
        create_autospec(storage.Client.bucket, side_effect=mock_get_bucket),
        base_gcs_client_mock,
    )

    # Helper function to create a new blob
    def create_mock_blob(blob_name):
        """Creates a new mock blob with all required methods and attributes."""
        mock_blob = create_autospec(storage.Blob)
        mock_blob.name = blob_name
        mock_blob.exists.return_value = True
        mock_blob.size = len(file_content)

        # Configure download_as_bytes with proper method binding
        def mock_download_as_bytes(
            self, client=None, start=None, end=None, raw_download=False, **kwargs
        ):
            """Mock implementation of download_as_bytes method.
            Cannot use autospec because it is bound to the mock_blob instance.
            """
            return file_content

        mock_blob.download_as_bytes = types.MethodType(
            mock_download_as_bytes, mock_blob
        )

        def mock_download_to_file(self, fileobj, *args, **kwargs):
            """Mock implementation of download_to_file method.
            Cannot use autospec because it is bound to the mock_blob instance.
            """
            fileobj.write(file_content)
            fileobj.seek(0)
            return None

        mock_blob.download_to_file = types.MethodType(mock_download_to_file, mock_blob)

        def mock_upload_from_file(
            self,
            file_obj,
            content_type=None,
            num_retries=None,
            client=None,
            size=None,
            **kwargs,
        ):
            """Simulates uploading a file to the blob, storing it in the blobs dictionary."""
            blobs[blob_name] = self
            return None

        def mock_upload_from_string(
            self,
            data,
            content_type=None,
            num_retries=None,
            client=None,
            **kwargs,
        ):
            """Simulates uploading string/bytes data to the blob, storing it in the blobs dictionary."""
            blobs[blob_name] = self
            return None

        def mock_generate_signed_url(self, version, expiration, method, **kwargs):
            """Generates a signed URL for the blob, raising NotFound if the blob doesn't exist."""
            if blob_name not in blobs:
                raise NotFound(f"Blob {blob_name} not found")
            return f"https://storage.googleapis.com/{mock_bucket.name}/{blob_name}"

        def mock_delete(self):
            """Deletes the blob from the blobs dictionary."""
            if blob_name in blobs:
                del blobs[blob_name]
            return None

        def mock_reload(self):
            """Simulates reloading the blob's metadata, raising NotFound if the blob doesn't exist."""
            if blob_name not in blobs:
                raise NotFound(f"Blob {blob_name} not found")
            return None

        # Create properly autospecced methods with side effects
        mock_blob.upload_from_file = types.MethodType(
            create_autospec(
                storage.Blob.upload_from_file, side_effect=mock_upload_from_file
            ),
            mock_blob,
        )
        mock_blob.upload_from_string = types.MethodType(
            create_autospec(
                storage.Blob.upload_from_string, side_effect=mock_upload_from_string
            ),
            mock_blob,
        )
        mock_blob.generate_signed_url = types.MethodType(
            create_autospec(
                storage.Blob.generate_signed_url, side_effect=mock_generate_signed_url
            ),
            mock_blob,
        )
        mock_blob.delete = types.MethodType(
            create_autospec(storage.Blob.delete, side_effect=mock_delete), mock_blob
        )
        mock_blob.reload = types.MethodType(
            create_autospec(storage.Blob.reload, side_effect=mock_reload), mock_blob
        )
        return mock_blob

    # Override the bucket's blob method to use our blob creation
    def mock_create_blob(self, blob_name, *args, **kwargs):
        """Creates a new blob in the bucket using the create_mock_blob helper."""
        return create_mock_blob(blob_name)

    mock_bucket.blob = types.MethodType(
        create_autospec(storage.Bucket.blob, side_effect=mock_create_blob), mock_bucket
    )

    return base_gcs_client_mock
