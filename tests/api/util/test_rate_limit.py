from unittest import mock

import pytest
from fastapi import Request

from fides.api.util.rate_limit import get_client_ip_from_header, validate_client_ip


class TestValidateClientIp:
    @pytest.mark.parametrize(
        "ip, expected",
        [
            ("198.51.100.10", True),
            ("2001:db8::1", True),
            ("127.0.0.1", False),  # Loopback
            ("172.16.0.1", False),  # Private
            ("192.168.1.100", False),  # Private
            ("10.0.0.5", False),  # Private
            ("169.254.1.1", False),  # Link-local
            ("::1", False),  # Loopback IPv6
            ("fe80::1", False),  # Link-local IPv6
            ("fc00::1", False),  # Unique Local IPv6
            ("224.0.0.1", False),  # Multicast
            ("not an ip", False),
            ("", False),
        ],
    )
    def test_validate_client_ip(self, ip, expected):
        assert validate_client_ip(ip) is expected


class TestGetClientIpFromHeader:
    def test_get_client_ip_from_header_configured_and_present(self, config):
        original_header = config.security.rate_limit_client_ip_header
        config.security.rate_limit_client_ip_header = "X-Forwarded-For"
        try:
            mock_request = mock.Mock(spec=Request)
            mock_request.headers = {"X-Forwarded-For": "198.51.100.10"}
            mock_request.client.host = "127.0.0.1"
            assert get_client_ip_from_header(mock_request) == "198.51.100.10"
        finally:
            config.security.rate_limit_client_ip_header = original_header

    def test_get_client_ip_from_header_with_port(self, config):
        original_header = config.security.rate_limit_client_ip_header
        config.security.rate_limit_client_ip_header = "X-Real-IP"
        try:
            mock_request = mock.Mock(spec=Request)
            mock_request.headers = {"X-Real-IP": "198.51.100.10:46532"}
            mock_request.client.host = "127.0.0.1"
            assert get_client_ip_from_header(mock_request) == "198.51.100.10"
        finally:
            config.security.rate_limit_client_ip_header = original_header

    def test_get_client_ip_from_header_missing(self, config):
        original_header = config.security.rate_limit_client_ip_header
        config.security.rate_limit_client_ip_header = "X-Forwarded-For"
        try:
            mock_request = mock.Mock(spec=Request)
            mock_request.headers = {}
            mock_request.client.host = "192.0.2.1"
            assert get_client_ip_from_header(mock_request) == "192.0.2.1"
        finally:
            config.security.rate_limit_client_ip_header = original_header

    def test_get_client_ip_from_header_mismatch(self, config):
        original_header = config.security.rate_limit_client_ip_header
        config.security.rate_limit_client_ip_header = "CloudFront-Viewer-Address"
        try:
            mock_request = mock.Mock(spec=Request)
            mock_request.headers = {"X-Forwarded-For": "198.51.100.10:46532"}
            mock_request.client.host = "192.0.2.1"
            assert get_client_ip_from_header(mock_request) == "192.0.2.1"
        finally:
            config.security.rate_limit_client_ip_header = original_header

    def test_get_client_ip_header_not_configured(self, config):
        original_header = config.security.rate_limit_client_ip_header
        config.security.rate_limit_client_ip_header = None
        try:
            mock_request = mock.Mock(spec=Request)
            mock_request.headers = {"X-Forwarded-For": "198.51.100.10"}
            mock_request.client.host = "192.0.2.1"
            assert get_client_ip_from_header(mock_request) == "192.0.2.1"
        finally:
            config.security.rate_limit_client_ip_header = original_header

    def test_get_client_ip_from_header_invalid_ip(self, config):
        original_header = config.security.rate_limit_client_ip_header
        config.security.rate_limit_client_ip_header = "X-Forwarded-For"
        try:
            mock_request = mock.Mock(spec=Request)
            mock_request.headers = {"X-Forwarded-For": "127.0.0.1"}
            mock_request.client.host = "192.0.2.1"
            assert get_client_ip_from_header(mock_request) == "192.0.2.1"
        finally:
            config.security.rate_limit_client_ip_header = original_header

    def test_get_client_ip_from_header_leftmost_ip_fallback(self, config):
        original_header = config.security.rate_limit_client_ip_header
        config.security.rate_limit_client_ip_header = "X-Forwarded-For"
        try:
            mock_request = mock.Mock(spec=Request)
            mock_request.headers = {"X-Forwarded-For": "203.0.113.195, 70.41.3.18"}
            mock_request.client.host = "192.0.2.1"
            assert get_client_ip_from_header(mock_request) == "192.0.2.1"
        finally:
            config.security.rate_limit_client_ip_header = original_header
