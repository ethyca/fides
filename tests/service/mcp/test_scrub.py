import pytest

from fides.service.mcp.scrub import RegexScrubber, Scrubber


def test_scrubber_is_protocol_runtime_checkable():
    s = RegexScrubber()
    assert isinstance(s, Scrubber)


def test_email_scrubbed():
    s = RegexScrubber()
    out = s.scrub("contact jane.doe+work@example.com please")
    assert "<email>" in out.scrubbed_text
    assert "jane.doe" not in out.scrubbed_text


def test_phone_e164_scrubbed():
    s = RegexScrubber()
    out = s.scrub("call +14155552671")
    assert "<phone>" in out.scrubbed_text


def test_us_ssn_scrubbed():
    s = RegexScrubber()
    out = s.scrub("ssn 123-45-6789 here")
    assert "<gov_id>" in out.scrubbed_text
    assert "123-45-6789" not in out.scrubbed_text


def test_credit_card_luhn_valid_scrubbed():
    s = RegexScrubber()
    # 4111 1111 1111 1111 is a known Luhn-valid test card
    out = s.scrub("card 4111-1111-1111-1111 expires soon")
    assert "<payment_card>" in out.scrubbed_text


def test_credit_card_luhn_invalid_not_scrubbed():
    s = RegexScrubber()
    out = s.scrub("invoice 4111-1111-1111-1112")
    assert "<payment_card>" not in out.scrubbed_text


def test_ipv4_scrubbed():
    s = RegexScrubber()
    out = s.scrub("client 192.168.1.42")
    assert "<ip_address>" in out.scrubbed_text


def test_long_opaque_token_scrubbed():
    s = RegexScrubber()
    token = "a" * 40  # 40 hex chars
    out = s.scrub(f"key={token}")
    assert "<token>" in out.scrubbed_text


def test_hash_stable_across_pii_changes():
    s = RegexScrubber()
    a = s.scrub("user=alice@example.com")
    b = s.scrub("user=bob@example.com")
    assert a.scrubbed_hash == b.scrubbed_hash


def test_hash_changes_with_structure():
    s = RegexScrubber()
    a = s.scrub("user=alice@example.com")
    b = s.scrub("user=alice@example.com&op=delete")
    assert a.scrubbed_hash != b.scrubbed_hash


def test_scrub_dict_recurses_string_leaves():
    s = RegexScrubber()
    out = s.scrub_dict({"user": "x@y.com", "id": "abc", "meta": {"phone": "+14155552671"}})
    assert "<email>" in out.scrubbed_text
    assert "<phone>" in out.scrubbed_text


def test_scrub_dict_handles_nested_lists():
    s = RegexScrubber()
    out = s.scrub_dict({"emails": ["a@b.com", "c@d.com"]})
    assert out.scrubbed_text.count("<email>") == 2
