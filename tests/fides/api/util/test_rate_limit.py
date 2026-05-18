import pytest

from fides.api.util.rate_limit import (
    _extract_hostname_from_ip,
    extract_and_validate_ip,
    validate_client_ip,
)


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


class TestExtractAndValidateIp:
    """Tests for the shared IP extraction and validation helper."""

    @pytest.mark.parametrize(
        "ip_value, expected_ip",
        [
            # Valid public IPv4
            ("150.51.100.10", "150.51.100.10"),
            ("8.8.8.8", "8.8.8.8"),
            # Valid public IPv4 with port
            ("150.51.100.10:46532", "150.51.100.10"),
            # Valid public IPv6
            ("2001:4860:4860::8888", "2001:4860:4860::8888"),
            ("2606:4700:4700::1111", "2606:4700:4700::1111"),
            # Valid public IPv6 with port
            ("[2001:4860:4860::8888]:443", "2001:4860:4860::8888"),
        ],
    )
    def test_valid_ips(self, ip_value, expected_ip):
        is_valid, extracted_ip = extract_and_validate_ip(ip_value)
        assert is_valid is True
        assert extracted_ip == expected_ip

    @pytest.mark.parametrize(
        "ip_value",
        [
            # Private IPs
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            # Loopback
            "127.0.0.1",
            "::1",
            # Reserved
            "198.51.100.10",
            "2001:db8::1",
            # Link-local
            "169.254.1.1",
            "fe80::1",
            # Malformed
            "not-an-ip",
            # Multiple IPs
            "203.0.113.195, 70.41.3.18",
            # Empty
            "",
        ],
    )
    def test_invalid_ips(self, ip_value):
        is_valid, extracted_ip = extract_and_validate_ip(ip_value)
        assert is_valid is False
        assert extracted_ip is None
