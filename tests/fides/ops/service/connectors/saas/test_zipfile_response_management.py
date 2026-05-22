"""
Tests that the zipfile response is handled correctly by the AuthenticatedClient.

This is to check that we are not impeded by the utf-8 decoding error when we receive a zipfile as a response.
"""

import io
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import pytest

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.schemas.saas.saas_config import ClientConfig
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient


class ZipFileHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves ZIP files for testing."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/test.zip":
            # Create a ZIP file in memory with UTF-8 problematic content
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add a file with content that would cause UTF-8 errors
                zip_file.writestr("test.txt", "Hello World!")
                # Add binary data that would fail UTF-8 decoding
                zip_file.writestr(
                    "binary.dat", b"\xe1\x93\x5e\x5b\x00\x01\x02\x03\xff\xfe"
                )

            zip_content = zip_buffer.getvalue()

            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(zip_content)))
            self.end_headers()
            self.wfile.write(zip_content)

        elif self.path == "/corrupted.zip":
            # Create corrupted ZIP-like content that would cause UTF-8 errors
            corrupted_content = (
                b"PK\x03\x04\x14\x00\x00\x08\x00\x00"  # Valid ZIP header (10 bytes)
                b"\xe1\x93"  # Invalid UTF-8 bytes at position 10-11 (same as Bazaarvoice error)
                b"\x5e\x5b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"corrupted_data_here\x00\x00\x00\x00"
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(corrupted_content)))
            self.end_headers()
            self.wfile.write(corrupted_content)

        elif self.path == "/empty.zip":
            # Create empty ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED):
                pass  # Empty ZIP

            zip_content = zip_buffer.getvalue()

            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(zip_content)))
            self.end_headers()
            self.wfile.write(zip_content)

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


@pytest.fixture(scope="class")
def zip_test_server():
    """Start a local HTTP server that serves ZIP files for testing."""
    server = HTTPServer(("localhost", 0), ZipFileHTTPHandler)
    port = server.server_address[1]

    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # Give server time to start
    time.sleep(0.1)

    yield f"http://localhost:{port}"

    server.shutdown()


@pytest.mark.integration
class TestZipFileResponseManagement:
    """Test ZIP file response handling with controlled test servers."""

    @pytest.fixture
    def test_connection_config(self, db, zip_test_server):
        """Create a connection config for testing."""
        parsed_url = urlparse(zip_test_server)
        return ConnectionConfig.create(
            db=db,
            data={
                "key": "zip_test",
                "name": "ZIP Test Server",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {
                    "domain": parsed_url.netloc,
                    "api_token": "test_token_123",
                },
            },
        )

    @pytest.fixture
    def test_client_config(self, zip_test_server):
        """Create a client config for testing."""
        parsed_url = urlparse(zip_test_server)
        return ClientConfig(
            protocol=parsed_url.scheme,
            host=parsed_url.netloc,
            authentication={
                "strategy": "bearer",
                "configuration": {"token": "<api_token>"},
            },
        )

    @pytest.fixture
    def authenticated_client(
        self, test_connection_config, test_client_config, zip_test_server
    ):
        """Create an AuthenticatedClient for testing."""
        return AuthenticatedClient(
            uri=zip_test_server,
            configuration=test_connection_config,
            client_config=test_client_config,
        )

    def test_valid_zip_file_download(self, authenticated_client):
        """
        Test downloading a valid ZIP file and verify it's handled correctly as binary data.

        This test ensures that:
        1. AuthenticatedClient can download ZIP files
        2. Binary content is preserved without UTF-8 decoding attempts
        3. ZIP file structure is maintained
        """
        request_params = SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/test.zip",
            headers={},
            query_params={},
        )

        response = authenticated_client.send(request_params)

        # Verify successful download
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/zip"
        assert len(response.content) > 0

        # Verify it's binary content (bytes)
        assert isinstance(response.content, bytes)

        # Verify it's a valid ZIP file
        assert response.content.startswith(b"PK"), (
            "Content should start with ZIP signature"
        )

        # Verify we can read the ZIP file
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            file_list = zip_file.namelist()
            assert "test.txt" in file_list
            assert "binary.dat" in file_list

            # Read the text file
            text_content = zip_file.read("test.txt").decode("utf-8")
            assert text_content == "Hello World!"

            # Read the binary file (this contains the problematic UTF-8 bytes)
            binary_content = zip_file.read("binary.dat")
            assert binary_content == b"\xe1\x93\x5e\x5b\x00\x01\x02\x03\xff\xfe"

        # Verify that trying to decode the entire ZIP as UTF-8 fails (as expected)
        with pytest.raises(UnicodeDecodeError) as exc_info:
            response.content.decode("utf-8")

        # This should be the same type of error as in Bazaarvoice logs
        assert "invalid continuation byte" in str(
            exc_info.value
        ) or "invalid start byte" in str(exc_info.value)

    def test_corrupted_zip_file_download(self, authenticated_client):
        """
        Test downloading corrupted ZIP-like content that mimics the Bazaarvoice error.

        This test reproduces the exact UTF-8 error scenario:
        - Content starts with ZIP signature (PK)
        - Contains invalid UTF-8 bytes at position 10-11
        - Should be handled as binary data without decoding attempts
        """
        request_params = SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/corrupted.zip",
            headers={},
            query_params={},
        )

        response = authenticated_client.send(request_params)

        # Verify successful download
        assert response.status_code == 200
        assert len(response.content) > 0

        # Verify it starts with ZIP signature
        assert response.content.startswith(b"PK"), (
            "Content should start with ZIP signature"
        )

        # Verify the problematic bytes are at position 10-11 (same as Bazaarvoice error)
        problematic_bytes = response.content[10:12]
        assert problematic_bytes == b"\xe1\x93", (
            f"Expected problematic bytes at position 10-11, got {problematic_bytes.hex()}"
        )

        # Verify that UTF-8 decoding fails at the expected position
        with pytest.raises(UnicodeDecodeError) as exc_info:
            response.content.decode("utf-8")

        error = exc_info.value
        assert error.start == 10, (
            f"Expected UTF-8 error at position 10, got {error.start}"
        )
        assert error.end == 12, (
            f"Expected UTF-8 error end at position 12, got {error.end}"
        )
        assert "invalid continuation byte" in str(error)

        # The key test: AuthenticatedClient should handle this as binary data
        # without attempting UTF-8 decoding, so we should get the raw bytes
        assert isinstance(response.content, bytes)
        assert len(response.content) > 20  # Should have the full content

    def test_empty_zip_file_download(self, authenticated_client):
        """Test downloading an empty ZIP file."""
        request_params = SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/empty.zip",
            headers={},
            query_params={},
        )

        response = authenticated_client.send(request_params)

        # Verify successful download
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/zip"
        assert len(response.content) > 0  # Even empty ZIP has structure

        # Verify it's a valid empty ZIP
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            file_list = zip_file.namelist()
            assert len(file_list) == 0  # Empty ZIP
