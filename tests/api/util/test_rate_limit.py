from unittest import mock

import pytest
from fastapi import Request

from fides.api.util.rate_limit import (
    InvalidClientIPError,
    _extract_hostname_from_ip,
    get_client_ip_from_header,
    validate_client_ip,
)
from fides.config import CONFIG


@pytest.fixture(scope="function")
def set_rate_limit_client_ip_header_none(db):
    """Set the rate limit client IP header to None for the duration of a test."""
    original_value = CONFIG.security.rate_limit_client_ip_header
    CONFIG.security.rate_limit_client_ip_header = None
    yield
    CONFIG.security.rate_limit_client_ip_header = original_value


@pytest.fixture(scope="function")
def set_rate_limit_client_ip_header_x_real_ip(db):
    """Set the rate limit client IP header to X-Real-IP for the duration of a test."""
    original_value = CONFIG.security.rate_limit_client_ip_header
    CONFIG.security.rate_limit_client_ip_header = "X-Real-IP"
    yield
    CONFIG.security.rate_limit_client_ip_header = original_value


@pytest.fixture(scope="function")
def set_rate_limit_client_ip_header_cloudfront_viewer_address(db):
    """Set the rate limit client IP header to CloudFront-Viewer-Address for the duration of a test."""
    original_value = CONFIG.security.rate_limit_client_ip_header
    CONFIG.security.rate_limit_client_ip_header = "CloudFront-Viewer-Address"
    yield
    CONFIG.security.rate_limit_client_ip_header = original_value


class TestValidateClientIp:
    @pytest.mark.parametrize(
        "ip",
        [
            # Public IPv4 addresses
            "150.51.100.10",
            "8.8.8.8",
            # Public IPv6 addresses
            "2001:4860:4860::8888",
            "2606:4700:4700::1111",
        ],
    )
    def test_validate_client_ip_valid(self, ip):
        assert validate_client_ip(ip) is True

    @pytest.mark.parametrize(
        "ip",
        [
            # Reserved/private/special addresses
            "198.51.100.10",  # Reserved
            "2001:db8::1",  # Reserved IPv6
            "127.0.0.1",  # Loopback
            "172.16.0.1",  # Private
            "192.168.1.100",  # Private
            "10.0.0.5",  # Private
            "169.254.1.1",  # Link-local
            "::1",  # Loopback IPv6
            "fe80::1",  # Link-local IPv6
            "fc00::1",  # Unique Local IPv6
            "224.0.0.1",  # Multicast
            # Invalid formats
            "not an ip",
            "",
            # Multiple IPs
            "192.168.1.1, 192.168.1.2",
            # IP with port
            "192.168.1.1:8080",
        ],
    )
    def test_validate_client_ip_invalid(self, ip):
        assert validate_client_ip(ip) is False


class TestExtractIpFromValue:
    @pytest.mark.parametrize(
        "header_value, expected",
        [
            # IPv4 without port
            ("192.168.1.1", "192.168.1.1"),
            ("150.51.100.10", "150.51.100.10"),
            # IPv4 with port
            ("198.51.100.10:46532", "198.51.100.10"),
            ("192.168.1.1:8080", "192.168.1.1"),
            ("10.0.0.1:3000", "10.0.0.1"),
            # IPv6 without port
            ("2001:db8::1", "2001:db8::1"),
            ("2001:4860:4860::8888", "2001:4860:4860::8888"),
            ("::1", "::1"),
            ("fe80::1", "fe80::1"),
            # IPv6 with port (bracket notation)
            ("[2001:db8::1]:8080", "2001:db8::1"),
            ("[2001:4860:4860::8888]:443", "2001:4860:4860::8888"),
            ("[::1]:3000", "::1"),
            ("[fe80::1]:80", "fe80::1"),
            # Edge cases with whitespace
            ("  192.168.1.1:8080  ", "192.168.1.1"),
            ("  [2001:db8::1]:8080  ", "2001:db8::1"),
            ("  2001:db8::1  ", "2001:db8::1"),
            # Edge case port without IP
            (":8080", ""),
            # Cases that urlparse extracts but may be invalid (validation happens elsewhere)
            ("not-an-ip:8080", "not-an-ip"),  # Invalid IP with port
            ("not-an-ip", "not-an-ip"),  # Invalid IP without port
            (
                "192.168.1.1:8080:extra",
                "192.168.1.1",
            ),  # Extra colon - urlparse handles gracefully
            # Multiple values - urlparse takes first part before delimiter
            (
                "192.168.1.1, 192.168.1.2",
                "192.168.1.1, 192.168.1.2",
            ),  # Comma treated as part of hostname
            (
                "192.168.1.1 192.168.1.2",
                "192.168.1.1 192.168.1.2",
            ),  # Space treated as part of hostname
        ],
    )
    def test_extract_ip_from_value_success(self, header_value, expected):
        assert _extract_hostname_from_ip(header_value) == expected

    @pytest.mark.parametrize(
        "header_value",
        [
            # Cases where no hostname can be extracted
            "",  # Empty string
            " ",  # Just whitespace
        ],
    )
    def test_extract_ip_from_value_failure(self, header_value):
        with pytest.raises(ValueError, match="Could not parse IP from header value"):
            _extract_hostname_from_ip(header_value)


class TestGetClientIpFromHeader:
    @pytest.mark.usefixtures("set_rate_limit_client_ip_header_x_real_ip")
    def test_get_client_ip_from_header_configured_and_present(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {"X-Real-IP": "150.51.100.10"}
        mock_request.client.host = "127.0.0.1"
        try:
            result = get_client_ip_from_header(mock_request)
        except ValueError as err:  # explicit guard: should never raise ValueError
            pytest.fail(f"Unexpected ValueError: {err}")
        assert result == "150.51.100.10"

    @pytest.mark.usefixtures("set_rate_limit_client_ip_header_x_real_ip")
    def test_get_client_ip_from_header_with_port(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {"X-Real-IP": "150.51.100.10:46532"}
        mock_request.client.host = "127.0.0.1"
        try:
            result = get_client_ip_from_header(mock_request)
        except ValueError as err:
            pytest.fail(f"Unexpected ValueError: {err}")
        assert result == "150.51.100.10"

    @pytest.mark.usefixtures("set_rate_limit_client_ip_header_x_real_ip")
    def test_get_client_ip_from_header_ipv6_with_port(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {"X-Real-IP": "[2001:4860:4860::8888]:443"}
        mock_request.client.host = "127.0.0.1"
        try:
            result = get_client_ip_from_header(mock_request)
        except ValueError as err:
            pytest.fail(f"Unexpected ValueError: {err}")
        assert result == "2001:4860:4860::8888"

    @pytest.mark.usefixtures(
        "set_rate_limit_client_ip_header_cloudfront_viewer_address"
    )
    def test_get_client_ip_from_header_missing(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {}
        mock_request.client.host = "192.0.2.1"
        try:
            result = get_client_ip_from_header(mock_request)
        except ValueError as err:
            pytest.fail(f"Unexpected ValueError: {err}")
        assert result == "192.0.2.1"

    @pytest.mark.usefixtures(
        "set_rate_limit_client_ip_header_cloudfront_viewer_address"
    )
    def test_get_client_ip_from_header_mismatch(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {"X-Real-IP": "150.51.100.10:46532"}
        mock_request.client.host = "192.0.2.1"
        try:
            result = get_client_ip_from_header(mock_request)
        except ValueError as err:
            pytest.fail(f"Unexpected ValueError: {err}")
        assert result == "192.0.2.1"

    @pytest.mark.usefixtures("set_rate_limit_client_ip_header_none")
    def test_get_client_ip_header_not_configured(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {"CloudFront-Viewer-Address": "150.51.100.10"}
        mock_request.client.host = "192.0.2.1"
        try:
            result = get_client_ip_from_header(mock_request)
        except ValueError as err:
            pytest.fail(f"Unexpected ValueError: {err}")
        assert result == "192.0.2.1"

    @pytest.mark.usefixtures(
        "set_rate_limit_client_ip_header_cloudfront_viewer_address"
    )
    def test_get_client_ip_from_header_invalid_ip_raises_exception(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {
            "CloudFront-Viewer-Address": "127.0.0.1"
        }  # Loopback - invalid
        mock_request.client.host = "192.0.2.1"

        with pytest.raises(InvalidClientIPError) as exc_info:
            get_client_ip_from_header(mock_request)

        assert exc_info.value.detail == "Invalid IP address format"
        assert exc_info.value.header_value == "127.0.0.1"
        assert exc_info.value.header_name == "CloudFront-Viewer-Address"

    @pytest.mark.usefixtures(
        "set_rate_limit_client_ip_header_cloudfront_viewer_address"
    )
    def test_get_client_ip_from_header_multiple_ips_raises_exception(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {
            "CloudFront-Viewer-Address": "203.0.113.195, 70.41.3.18"
        }
        mock_request.client.host = "192.0.2.1"

        with pytest.raises(InvalidClientIPError) as exc_info:
            get_client_ip_from_header(mock_request)

        assert exc_info.value.detail == "Invalid IP address format"
        assert exc_info.value.header_value == "203.0.113.195, 70.41.3.18"
        assert exc_info.value.header_name == "CloudFront-Viewer-Address"

    @pytest.mark.usefixtures(
        "set_rate_limit_client_ip_header_cloudfront_viewer_address"
    )
    def test_get_client_ip_from_header_malformed_ip_raises_exception(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {"CloudFront-Viewer-Address": "not-an-ip"}
        mock_request.client.host = "192.0.2.1"

        with pytest.raises(InvalidClientIPError) as exc_info:
            get_client_ip_from_header(mock_request)

        assert exc_info.value.detail == "Invalid IP address format"
        assert exc_info.value.header_value == "not-an-ip"
        assert exc_info.value.header_name == "CloudFront-Viewer-Address"

    @pytest.mark.usefixtures(
        "set_rate_limit_client_ip_header_cloudfront_viewer_address"
    )
    def test_get_client_ip_from_header_private_ip_raises_exception(self, config):
        mock_request = mock.Mock(spec=Request)
        mock_request.headers = {
            "CloudFront-Viewer-Address": "192.168.1.1"
        }  # Private IP
        mock_request.client.host = "192.0.2.1"

        with pytest.raises(InvalidClientIPError) as exc_info:
            get_client_ip_from_header(mock_request)

        assert exc_info.value.detail == "Invalid IP address format"
        assert exc_info.value.header_value == "192.168.1.1"
        assert exc_info.value.header_name == "CloudFront-Viewer-Address"
