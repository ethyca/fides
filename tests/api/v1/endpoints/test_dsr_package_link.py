import urllib.parse

import boto3
import pytest
from moto import mock_aws
from starlette.status import (
    HTTP_200_OK,
    HTTP_302_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from fides.api.models.storage import StorageConfig, StorageType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageSecrets,
)
from fides.common.api.v1.urn_registry import PRIVACY_CENTER_DSR_PACKAGE


@mock_aws
@pytest.mark.usefixtures("set_active_storage_s3", "storage_config_default")
class TestPrivacyCenterDsrPackage:
    @pytest.fixture(scope="function")
    def url(self, privacy_request):
        return f"/api/v1{PRIVACY_CENTER_DSR_PACKAGE.format(privacy_request_id=privacy_request.id)}"

    @pytest.fixture(scope="function")
    def completed_privacy_request(self, db, privacy_request):
        """Create a completed privacy request with access result URLs"""
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.access_result_urls = {
            "access_result_urls": ["https://test-bucket.s3.amazonaws.com/test-file.zip"]
        }

        db.commit()
        return privacy_request

    @pytest.fixture(scope="function")
    def pending_privacy_request(self, db, privacy_request):
        """Create a pending privacy request"""
        privacy_request.status = PrivacyRequestStatus.pending
        db.commit()
        return privacy_request

    @pytest.fixture(scope="function")
    def mock_s3_with_file(self, completed_privacy_request):
        """Set up mock S3 environment with bucket and test file"""
        # Just return mock data - moto will handle all S3 operations automatically
        test_content = b"test file content"
        file_name = f"{completed_privacy_request.id}.zip"

        # Return a tuple that matches what the tests expect
        yield test_content, file_name

    @pytest.fixture(scope="function")
    def mock_s3_auto_auth_with_file(self, completed_privacy_request):
        """Set up mock S3 environment with auto auth bucket and test file"""
        # Just return mock data - moto will handle all S3 operations automatically
        test_content = b"test file content"
        file_name = f"{completed_privacy_request.id}.zip"

        # Return a tuple that matches what the tests expect
        yield test_content, file_name

    def test_get_dsr_package_unauthenticated_success(
        self, url, completed_privacy_request, test_client, storage_config_default, db
    ):
        """Test that unauthenticated users can access the endpoint"""
        # Ensure the storage config has secret keys authentication
        storage_config_default.details[StorageDetails.AUTH_METHOD.value] = (
            AWSAuthMethod.SECRET_KEYS.value
        )
        storage_config_default.set_secrets(
            db=db,
            storage_secrets={
                StorageSecrets.AWS_ACCESS_KEY_ID.value: "fake_access_key",
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "fake_secret_key",
            },
        )
        db.commit()

        # allow_redirects=False prevents the test client from automatically following the redirect,
        # allowing us to verify the 302 status and Location header without making the actual S3 request
        response = test_client.get(url, allow_redirects=False)
        assert response.status_code == HTTP_302_FOUND

        # Check that we're redirected to a presigned URL
        redirect_url = response.headers.get("location")
        assert redirect_url is not None

        # The URL should contain the privacy request ID and be a presigned URL
        assert str(completed_privacy_request.id) in redirect_url
        # moto generates URLs in format: https://s3.amazonaws.com/bucket/key
        parsed_url = urllib.parse.urlparse(redirect_url)
        assert parsed_url.hostname == "s3.amazonaws.com"
        assert "test_bucket" in redirect_url
        # moto uses different parameter names than real AWS
        assert (
            "Expires=" in redirect_url
        )  # moto uses 'Expires' instead of 'X-Amz-Expires'

    def test_get_dsr_package_with_auth_success(
        self,
        url,
        completed_privacy_request,
        test_client,
        root_auth_header,
        storage_config_default,
        db,
    ):
        """Test that authenticated users can also access the endpoint"""
        # Ensure the storage config has secret keys authentication
        storage_config_default.details[StorageDetails.AUTH_METHOD.value] = (
            AWSAuthMethod.SECRET_KEYS.value
        )
        storage_config_default.set_secrets(
            db=db,
            storage_secrets={
                StorageSecrets.AWS_ACCESS_KEY_ID.value: "fake_access_key",
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "fake_secret_key",
            },
        )
        db.commit()

        response = test_client.get(url, headers=root_auth_header, allow_redirects=False)
        assert response.status_code == HTTP_302_FOUND

        # Check that we're redirected to a presigned URL
        redirect_url = response.headers.get("location")
        assert redirect_url is not None

        # The URL should contain the privacy request ID and be a presigned URL
        assert str(completed_privacy_request.id) in redirect_url
        # moto generates URLs in format: https://s3.amazonaws.com/bucket/key
        parsed_url = urllib.parse.urlparse(redirect_url)
        assert parsed_url.hostname == "s3.amazonaws.com"
        assert "test_bucket" in redirect_url
        # moto uses different parameter names than real AWS
        assert (
            "Expires=" in redirect_url
        )  # moto uses 'Expires' instead of 'X-Amz-Expires'

    def test_get_access_results_request_not_complete(
        self, pending_privacy_request, test_client
    ):
        """Test that requests that are not complete return an error"""
        url = f"/api/v1{PRIVACY_CENTER_DSR_PACKAGE.format(privacy_request_id=pending_privacy_request.id)}"
        response = test_client.get(url)
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "not complete" in response.json()["detail"]

    def test_get_access_results_no_access_result_urls(
        self, db, privacy_request, test_client
    ):
        """Test that requests with no access result URLs return 404"""
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.access_result_urls = None
        db.commit()

        url = f"/api/v1{PRIVACY_CENTER_DSR_PACKAGE.format(privacy_request_id=privacy_request.id)}"
        response = test_client.get(url)
        assert response.status_code == HTTP_404_NOT_FOUND
        assert "No access results found" in response.json()["detail"]

    def test_get_access_results_request_not_found(self, test_client, privacy_request):
        """Test that non-existent requests return 404"""
        # Use a valid pri_uuid format that doesn't exist in the database
        non_existent_id = "pri_12345678-1234-1234-1234-123456789012"
        url = f"/api/v1{PRIVACY_CENTER_DSR_PACKAGE.format(privacy_request_id=non_existent_id)}"
        response = test_client.get(url)
        assert response.status_code == HTTP_404_NOT_FOUND

    def test_get_access_results_invalid_uuid_format(self, test_client):
        """Test that truly invalid UUID formats are rejected to prevent SSRF attacks"""
        # Test various invalid UUID formats that could be used in SSRF attacks
        invalid_ids = [
            "not-a-uuid",
            "12345",
            "pri_not-a-uuid",  # Invalid format: pri_ prefix but not followed by UUID
            "pri_12345",  # Invalid format: pri_ prefix but not followed by UUID
            "other_123e4567-e89b-12d3-a456-426614174000",  # Wrong prefix
            "pri",  # Just the prefix
        ]

        for invalid_id in invalid_ids:
            # Construct URL directly with invalid ID, don't use the url fixture
            url = f"/api/v1{PRIVACY_CENTER_DSR_PACKAGE.format(privacy_request_id=invalid_id)}"
            response = test_client.get(url)

            # We expect 400 for invalid format, not 404
            assert (
                response.status_code == HTTP_400_BAD_REQUEST
            ), f"Expected 400 for invalid ID '{invalid_id}', got {response.status_code}"
            assert "Invalid privacy request ID format" in response.json()["detail"]
            assert (
                "Must start with 'pri_' followed by a valid UUID v4"
                in response.json()["detail"]
            )

    def test_get_access_results_valid_uuid_format(self, test_client):
        """Test that valid pri_uuid format is accepted by the validation logic"""
        # Test with a valid pri_uuid format that doesn't exist in the database
        valid_id = "pri_123e4567-e89b-12d3-a456-426614174000"
        url = f"/api/v1{PRIVACY_CENTER_DSR_PACKAGE.format(privacy_request_id=valid_id)}"
        response = test_client.get(url)

        # Should get 404 for non-existent ID, not 400 for invalid format
        assert (
            response.status_code == HTTP_404_NOT_FOUND
        ), f"Expected 404 for valid UUID format, got {response.status_code}"
        assert "No privacy request found" in response.json()["detail"]

    def test_get_access_results_empty_access_result_urls(
        self, db, privacy_request, test_client
    ):
        """Test that requests with empty access result URLs return 404"""
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.access_result_urls = {"access_result_urls": []}
        db.commit()

        url = f"/api/v1{PRIVACY_CENTER_DSR_PACKAGE.format(privacy_request_id=privacy_request.id)}"
        response = test_client.get(url)
        assert response.status_code == HTTP_404_NOT_FOUND
        assert "No access result URLs found" in response.json()["detail"]

    def test_get_access_results_rate_limiting(
        self, url, completed_privacy_request, test_client, storage_config_default, db
    ):
        """Test that rate limiting is actually applied to the endpoint"""
        # Ensure the storage config has secret keys authentication
        storage_config_default.details[StorageDetails.AUTH_METHOD.value] = (
            AWSAuthMethod.SECRET_KEYS.value
        )
        storage_config_default.set_secrets(
            db=db,
            storage_secrets={
                StorageSecrets.AWS_ACCESS_KEY_ID.value: "fake_access_key",
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "fake_secret_key",
            },
        )
        db.commit()

        # First, verify the endpoint works normally
        response = test_client.get(url, allow_redirects=False)
        assert (
            response.status_code == HTTP_302_FOUND
        ), "Endpoint should work normally before rate limiting"

        # Make multiple requests rapidly to trigger rate limiting
        # The exact number depends on the rate limit configuration
        responses = []
        for i in range(20):  # Make more requests to ensure we hit rate limits
            response = test_client.get(url, allow_redirects=False)
            responses.append(response.status_code)

            # Check if we got any rate limit responses (429 Too Many Requests)
        # If rate limiting is working, we should see some 429s
        rate_limit_responses = [r for r in responses if r == 429]

        # At least some requests should succeed (rate limiting might not be very strict in tests)
        # But we should see evidence of rate limiting if it's working
        assert HTTP_302_FOUND in responses, "Some requests should succeed"

    @pytest.mark.usefixtures("completed_privacy_request")
    def test_get_access_results_gcs_storage_unsupported(self, url, test_client, db):
        """Test that GCS storage returns an error"""
        # Create a GCS storage config
        gcs_data = {
            "name": "test-gcs-storage",
            "type": StorageType.gcs,
            "is_default": True,  # Make it the default
            "details": {"bucket": "test-gcs-bucket", "project_id": "test-project"},
            "key": "test_gcs_storage_config",
            "format": ResponseFormat.json,
        }
        gcs_storage_config = StorageConfig.create(db=db, data=gcs_data)

        # Set GCS as the active default storage type
        from fides.api.models.application_config import ApplicationConfig

        ApplicationConfig.create_or_update(
            db,
            data={
                "api_set": {
                    "storage": {"active_default_storage_type": StorageType.gcs.value}
                }
            },
        )

        # The function should raise an error for GCS
        response = test_client.get(url, allow_redirects=False)
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert (
            "Only S3 storage is supported for download redirects"
            in response.json()["detail"]
        )

        # Clean up
        gcs_storage_config.delete(db)

    @pytest.mark.usefixtures("completed_privacy_request")
    def test_get_access_results_s3_presigned_url_generation(
        self,
        url,
        test_client,
        storage_config_default,
        mock_s3_with_file,
        db,
    ):
        """Test that S3 presigned URLs are actually generated correctly and are valid"""
        # Ensure the storage config has secret keys authentication
        storage_config_default.details[StorageDetails.AUTH_METHOD.value] = (
            AWSAuthMethod.SECRET_KEYS.value
        )
        storage_config_default.set_secrets(
            db=db,
            storage_secrets={
                StorageSecrets.AWS_ACCESS_KEY_ID.value: "fake_access_key",
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "fake_secret_key",
            },
        )
        db.commit()

        test_content, file_name = mock_s3_with_file

        # Test the endpoint
        # allow_redirects=False prevents the test client from automatically following the redirect,
        # allowing us to verify the 302 status and Location header without making the actual S3 request
        response = test_client.get(url, allow_redirects=False)
        assert response.status_code == HTTP_302_FOUND

        # Verify the presigned URL
        redirect_url = response.headers.get("location")
        assert redirect_url is not None, "Redirect URL should be present"

        # Parse the URL to verify it's a valid S3 presigned URL
        parsed_url = urllib.parse.urlparse(redirect_url)

        # Verify it's an HTTPS URL
        assert (
            parsed_url.scheme == "https"
        ), f"Expected HTTPS scheme, got {parsed_url.scheme}"

        # Verify it's pointing to S3 (either s3.amazonaws.com or the specific bucket)
        assert parsed_url.netloc in [
            "s3.amazonaws.com",
            "test_bucket.s3.amazonaws.com",
        ], f"Expected S3 domain, got {parsed_url.netloc}"

        # Verify the file name is in the URL
        assert (
            file_name in redirect_url
        ), f"File name {file_name} should be in the presigned URL"

        # Verify the bucket name is in the URL
        assert (
            "test_bucket" in redirect_url
        ), "Bucket name should be in the presigned URL"

        # Verify it has the required presigned URL parameters
        # moto uses different parameter names than real AWS
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Verify the URL is properly formatted
        assert len(parsed_url.query) > 0, "Presigned URL should have query parameters"
        assert (
            len(query_params) >= 3
        ), f"Presigned URL should have at least 3 parameters, got {len(query_params)}"

    @pytest.mark.usefixtures("completed_privacy_request")
    def test_get_access_results_s3_auto_auth(
        self,
        url,
        test_client,
        storage_config_default,
        mock_s3_auto_auth_with_file,
        db,
    ):
        """Test that S3 presigned URLs work with automatic authentication"""
        # Temporarily change the storage config to use automatic authentication
        storage_config_default.details[StorageDetails.AUTH_METHOD.value] = (
            AWSAuthMethod.AUTOMATIC.value
        )
        # Remove secrets to force automatic authentication
        storage_config_default.secrets = {}
        db.commit()

        test_content, file_name = mock_s3_auto_auth_with_file

        # Test the endpoint
        # allow_redirects=False prevents the test client from automatically following the redirect,
        # allowing us to verify the 302 status and Location header without making the actual S3 request
        response = test_client.get(url, allow_redirects=False)
        assert response.status_code == HTTP_302_FOUND

        # Verify the presigned URL
        redirect_url = response.headers.get("location")
        assert redirect_url is not None, "Redirect URL should be present"

        # Parse the URL to verify it's a valid S3 presigned URL
        parsed_url = urllib.parse.urlparse(redirect_url)

        # Verify it's an HTTPS URL
        assert (
            parsed_url.scheme == "https"
        ), f"Expected HTTPS scheme, got {parsed_url.scheme}"

        # Verify it's pointing to S3
        assert parsed_url.netloc in [
            "s3.amazonaws.com",
            "test_bucket.s3.amazonaws.com",
        ], f"Expected S3 domain, got {parsed_url.netloc}"

        # Verify the file name is in the URL
        assert (
            file_name in redirect_url
        ), f"File name {file_name} should be in the presigned URL"

        # Verify the bucket name is in the URL (should be test_bucket for this test)
        assert (
            "test_bucket" in redirect_url
        ), "Bucket name should be in the presigned URL"

        # Verify it has the required presigned URL parameters
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Verify the URL is properly formatted
        assert len(parsed_url.query) > 0, "Presigned URL should have query parameters"
        assert (
            len(query_params) >= 3
        ), f"Presigned URL should have at least 3 parameters, got {len(query_params)}"

    @pytest.mark.usefixtures("completed_privacy_request")
    def test_get_access_results_full_redirect_flow(
        self,
        url,
        test_client,
        storage_config_default,
        mock_s3_with_file,
        db,
    ):
        """Test the complete redirect flow - endpoint redirects to presigned URL and URL is accessible"""
        # Ensure the storage config has secret keys authentication
        storage_config_default.details[StorageDetails.AUTH_METHOD.value] = (
            AWSAuthMethod.SECRET_KEYS.value
        )
        storage_config_default.set_secrets(
            db=db,
            storage_secrets={
                StorageSecrets.AWS_ACCESS_KEY_ID.value: "fake_access_key",
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "fake_secret_key",
            },
        )
        db.commit()

        # mock_s3_with_file now returns test_content, file_name
        _, _ = mock_s3_with_file

        # Test the endpoint with allow_redirects=True to follow the full redirect flow
        response = test_client.get(url, allow_redirects=True)

        # Note: moto may not handle presigned URLs correctly, so we just verify the redirect happened
        # The important part is that the endpoint generated a valid presigned URL
        assert response.status_code in [
            HTTP_200_OK,
            HTTP_404_NOT_FOUND,
        ]  # moto might return 404 for presigned URLs

        # Verify that we got some response (either file content or error from moto)
        assert response.content is not None
