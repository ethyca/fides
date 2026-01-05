import re

from fides.api.util.security_headers import (
    HeaderRule,
    get_applicable_header_rules,
    is_exact_match,
)


class TestSecurityHeaders:
    def test_is_exact_match(self):
        assert is_exact_match(re.compile(r"\/example-path"), "/example-path") is True
        assert (
            is_exact_match(
                re.compile(r"\/example-path"), "/example-path/with-more-content"
            )
            is False
        )
        assert (
            is_exact_match(
                re.compile(r"\/example-path/?(.*)"), "/example-path/with-more-content"
            )
            is True
        )
        assert (
            is_exact_match(re.compile(r"\/example-path"), "/anti-example-path") is False
        )
        assert (
            is_exact_match(
                re.compile(r"\/example-path"), "/completely-disparate-no-match"
            )
        ) is False

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
