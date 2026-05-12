"""Tests for reply-to token generation and address formatting."""

import pytest

from fides.api.service.messaging.messaging_providers.reply_to_utils import (
    format_reply_to_address,
    generate_reply_to_token,
)


class TestGenerateReplyToToken:
    def test_token_is_32_hex_chars(self):
        token = generate_reply_to_token()
        assert len(token) == 32
        assert all(c in "0123456789abcdef" for c in token)

    def test_tokens_are_unique(self):
        """Smoke test: 128-bit tokens should never collide in 100 draws."""
        tokens = {generate_reply_to_token() for _ in range(100)}
        assert len(tokens) == 100


class TestFormatReplyToAddress:
    _VALID_TOKEN = "a" * 32

    def test_plus_addressing(self):
        address = format_reply_to_address(self._VALID_TOKEN, "example.com")
        assert address == f"reply+{self._VALID_TOKEN}@replies.example.com"

    def test_dedicated_subdomain(self):
        address = format_reply_to_address(
            self._VALID_TOKEN, "example.com", use_plus_addressing=False
        )
        assert address == f"{self._VALID_TOKEN}@replies.example.com"

    def test_with_real_token(self):
        token = generate_reply_to_token()
        address = format_reply_to_address(token, "example.com")
        assert address == f"reply+{token}@replies.example.com"
        assert len(token) == 32

    @pytest.mark.parametrize(
        "token",
        ["", "not-hex!", "abc\ninjection", "abc123", None],
        ids=["empty", "non-hex", "newline-injection", "too-short", "none"],
    )
    def test_invalid_token_raises(self, token):
        with pytest.raises(ValueError, match="Invalid reply-to token"):
            format_reply_to_address(token or "", "example.com")

    @pytest.mark.parametrize(
        "domain",
        [
            "",
            "evil.com\nBcc: attacker@evil.com",
            "has spaces.com",
            "has@at.com",
            "...",
            ".example.com",
            "example..com",
        ],
        ids=[
            "empty",
            "header-injection",
            "spaces",
            "at-sign",
            "only-dots",
            "leading-dot",
            "consecutive-dots",
        ],
    )
    def test_invalid_domain_raises(self, domain):
        with pytest.raises(ValueError, match="Invalid reply-to domain"):
            format_reply_to_address(self._VALID_TOKEN, domain)
