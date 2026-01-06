import re
from unittest import mock

import pytest
from fastapi import Request, Response

from fides.api.util.security_headers import (
    HeaderRule,
    apply_headers_to_response,
    get_applicable_header_rules,
    is_exact_match,
    recommended_csp_header_value,
    recommended_headers,
)


class TestSecurityHeaders:
    @pytest.mark.parametrize(
        "pattern,path,expected",
        [
            (r"\/example-path", "/example-path", True),
            (r"\/example-path", "/example-path/with-more-content", False),
            (r"\/example-path/?(.*)", "/example-path/with-more-content", True),
            (r"\/example-path", "/anti-example-path", False),
            (r"\/example-path", "/completely-disparate-no-match", False),
        ],
    )
    def test_is_exact_match(self, pattern, path, expected):
        assert (is_exact_match(pattern, path)) is expected

    def test_get_applicable_header_rules_returns_first_matching_rule_for_path(self):
        expected_headers: tuple[str, str] = ("header-1", "value-1")
        headers: list[HeaderRule] = [
            HeaderRule(re.compile(r"\/a"), [expected_headers]),
            HeaderRule(re.compile(r"\/a"), [("header-1", "value-2")]),
        ]

        assert get_applicable_header_rules("/a", headers) == [expected_headers]

    def test_get_applicable_header_rules_returns_disparate_headers(self):
        header1 = "header-1"
        header2 = "header-2"
        headers1: tuple[str, str] = (header1, "value-1")
        headers2: tuple[str, str] = (header2, "value-2")
        headers: list[HeaderRule] = [
            HeaderRule(re.compile(r"\/a-path"), [headers1]),
            HeaderRule(re.compile(r"\/a-path"), [headers2]),
        ]

        assert get_applicable_header_rules("/a-path", headers) == [headers1, headers2]

    def test_apply_headers_to_response(self):
        header = ("header-1", "value-1")
        header_rules: list[HeaderRule] = [HeaderRule(re.compile(r".*"), [header])]

        mock_request = mock.Mock(spec=Request)
        mock_request.url.path = "/any-path"

        response = Response()

        apply_headers_to_response(header_rules, mock_request, response)

        assert header in response.headers.items()

    @pytest.mark.parametrize(
        "path,expected",
        [
            (
                "/api/foo",
                [
                    ("X-Content-Type-Options", "nosniff"),
                    ("Strict-Transport-Security", "max-age=31536000"),
                ],
            ),
            (
                "/health",
                [
                    ("X-Content-Type-Options", "nosniff"),
                    ("Strict-Transport-Security", "max-age=31536000"),
                ],
            ),
            (
                "/privacy-requests",
                [
                    ("X-Content-Type-Options", "nosniff"),
                    ("Strict-Transport-Security", "max-age=31536000"),
                    (
                        "Content-Security-Policy",
                        recommended_csp_header_value,
                    ),
                    ("X-Frame-Options", "SAMEORIGIN"),
                ],
            ),
        ],
    )
    def test_recommended_headers_api_route(self, path, expected):
        applicable_rules = get_applicable_header_rules(path, recommended_headers)
        assert applicable_rules == expected
