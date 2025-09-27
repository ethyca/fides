import time
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock
from zipfile import ZipFile

from requests import PreparedRequest, Request

from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient


@dataclass
class MockResponse:
    """Structured response data for MockAuthenticatedClient."""

    json_data: Optional[Dict[str, Any]] = None
    binary_content: Optional[bytes] = None
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)

    @property
    def is_binary(self) -> bool:
        return self.binary_content is not None

    def __post_init__(self):
        """Set default headers if none provided."""
        if not self.headers:
            self.headers = {
                "content-type": (
                    "application/octet-stream" if self.is_binary else "application/json"
                )
            }


DEFAULT_POLLING_ERROR_MESSAGE = (
    "The endpoint did not return the required data for testing during the time limit"
)


def poll_for_existence(
    poller: Callable,
    args: List[Any] = (),
    kwargs: Dict[str, Any] = {},
    error_message: str = DEFAULT_POLLING_ERROR_MESSAGE,
    retries: int = 10,
    interval: int = 5,
    existence_desired=True,
    verification_count=1,
) -> Any:
    # we continue polling if poller is None OR if poller is not None but we don't desire existence, i.e. we are polling for removal
    original_retries = retries
    for _ in range(verification_count):
        while (return_val := poller(*args, **kwargs) is None) is existence_desired:
            if not retries:
                raise Exception(error_message)
            retries -= 1
            time.sleep(interval)
        retries = original_retries
    return return_val


class MockAuthenticatedClient(Mock):
    """
    Mock AuthenticatedClient that maps SaaSRequestParams to static responses.
    Based on the Fidesplus implementation but adapted for Fides tests.

    Supports both JSON and binary/attachment responses through a unified interface:

    JSON responses:
        client = MockAuthenticatedClient()
        client.add_response("GET", "/api/data", response={"items": [1, 2, 3]})

    Binary/attachment responses:
        client.add_response("GET", "/api/download", content=b"file content")

    Or use the convenience method:
        client.add_binary_response("GET", "/api/download", b"file content")
    """

    def __init__(self, *args, **kwargs):
        super().__init__(spec=AuthenticatedClient, *args, **kwargs)
        self.responses: Dict[Tuple[str, str, frozenset], List[MockResponse]] = {}
        self.call_counts: Dict[Tuple[str, str, frozenset], int] = {}
        self.send = MagicMock(side_effect=self._send)

    def add_response(
        self,
        method: str,
        path: str,
        response: Optional[Dict[str, Any]] = None,
        *,
        content: Optional[bytes] = None,
        query_params: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Maps the method and path to a response with status code and headers.

        Args:
            response: JSON response data (for regular API responses)
            content: Binary response data (for file/attachment responses)
            query_params: URL query parameters to match
            status_code: HTTP status code
            headers: HTTP response headers

        Note: Exactly one of 'response' or 'content' must be provided.
        If called multiple times for the same key, responses are stacked and returned in sequence.
        """
        if response is not None and content is not None:
            raise ValueError(
                "Cannot specify both 'response' and 'content' - use one or the other"
            )
        if response is None and content is None:
            raise ValueError(
                "Must specify either 'response' (for JSON) or 'content' (for binary)"
            )

        query_params = query_params or {}
        query_params_key = frozenset(query_params.items())
        key = (method, path, query_params_key)

        if key not in self.responses:
            self.responses[key] = []
            self.call_counts[key] = 0

        mock_response = MockResponse(
            json_data=response,
            binary_content=content,
            status_code=status_code,
            headers=headers or {},
        )
        self.responses[key].append(mock_response)

    def add_binary_response(
        self,
        method: str,
        path: str,
        content: bytes,
        query_params: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Convenience method for adding binary responses.
        This is just a wrapper around add_response(content=...).
        """
        self.add_response(
            method=method,
            path=path,
            content=content,
            query_params=query_params,
            status_code=status_code,
            headers=headers or {"content-type": "application/octet-stream"},
        )

    def get_authenticated_request(self, request_params: SaaSRequestParams):
        """Returns a PreparedRequest object with the expected attributes."""
        req: PreparedRequest = Request(
            method=request_params.method,
            url=f"https://example.com/{request_params.path}",
            headers=request_params.headers,
            params=request_params.query_params,
            data=request_params.body,
            files=request_params.files,
        ).prepare()

        return req

    def _send(self, params: SaaSRequestParams, ignore_errors=False):
        """Returns a stored response instead of making an actual HTTP request."""

        # Try to find a response without query params first in case they were not specified.
        for query_params_key in [frozenset(), frozenset(params.query_params.items())]:
            key = (params.method, params.path, query_params_key)

            if key in self.responses:
                responses = self.responses[key]
                call_count = self.call_counts[key]

                # If there's only one response, always return it
                if len(responses) == 1:
                    mock_response_data = responses[0]
                else:
                    # If there are multiple responses and we've gone beyond them, raise an exception
                    if call_count >= len(responses):
                        raise ValueError(
                            f"No more responses available for {key}. "
                            f"Called {call_count + 1} times but only {len(responses)} responses provided."
                        )
                    # Get the response for this call count
                    mock_response_data = responses[call_count]

                # Increment the call count for next time
                self.call_counts[key] += 1

                # Create mock response based on the structured data
                mock_response = Mock()
                mock_response.status_code = mock_response_data.status_code
                mock_response.headers = mock_response_data.headers
                mock_response.ok = mock_response_data.status_code < 400

                if mock_response_data.is_binary:
                    # Binary response
                    mock_response.content = mock_response_data.binary_content
                    mock_response.text = str(mock_response_data.binary_content)
                    mock_response.json.side_effect = ValueError(
                        "No JSON object could be decoded"
                    )
                else:
                    # JSON response
                    mock_response.json.return_value = mock_response_data.json_data
                    mock_response.text = str(mock_response_data.json_data)
                    mock_response.content = str(mock_response_data.json_data).encode(
                        "utf-8"
                    )

                return mock_response

        raise ValueError(f"No mock response for {key}")


def create_zip_file(file_data: Dict[str, str]) -> BytesIO:
    """
    Create a zip file in memory with the given files.

    Args:
        files (Dict[str, str]): A mapping of filenames to their contents

    Returns:
        io.BytesIO: An in-memory zip file with the specified files.
    """
    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, "w") as zip_file:
        for filename, file_content in file_data.items():
            zip_file.writestr(filename, file_content)

    # resetting the file position pointer to the beginning of the stream
    # so the tests can read the zip file from the beginning
    zip_buffer.seek(0)
    return zip_buffer
