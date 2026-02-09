"""Tests for version cleaning utility."""

import pytest

from fides.common.utils import clean_version


@pytest.mark.parametrize(
    "input_version,expected",
    [
        # Clean release tags - should remain unchanged
        ("2.78.0", "2.78.0"),
        ("2.99.0", "2.99.0"),
        ("3.0.0", "3.0.0"),
        # Pre-releases - should remain unchanged
        ("2.78.0a1", "2.78.0a1"),
        ("2.78.0a10", "2.78.0a10"),
        ("2.78.0b2", "2.78.0b2"),
        ("2.78.0rc1", "2.78.0rc1"),
        # Local builds with commits past a release tag - should remain unchanged
        ("2.78.0+4.gabcdef", "2.78.0+4.gabcdef"),
        ("2.78.0a1+5.gabcdef", "2.78.0a1+5.gabcdef"),
        ("2.78.0+123.g1234567", "2.78.0+123.g1234567"),
    ],
)
def testclean_versions_unchanged(input_version: str, expected: str) -> None:
    """Verify that clean version strings are not modified."""
    result = clean_version(input_version)
    assert result == expected


@pytest.mark.parametrize(
    "input_version,expected",
    [
        # Dot-separated dirty suffix
        ("2.99.0.dirty", "2.99.0"),
        ("2.78.0.dirty", "2.78.0"),
        ("2.78.0a1.dirty", "2.78.0a1"),
        # Hyphen-separated dirty suffix
        ("2.99.0-dirty", "2.99.0"),
        ("2.78.0-dirty", "2.78.0"),
        # Local builds with dirty suffix
        ("2.78.0+4.gabcdef.dirty", "2.78.0+4.gabcdef"),
        ("2.99.0-1-gabcdef-dirty", "2.99.0-1-gabcdef"),
        ("2.78.0a1+5.gabcdef.dirty", "2.78.0a1+5.gabcdef"),
    ],
)
def test_dirty_suffix_removed(input_version: str, expected: str) -> None:
    """Verify that dirty suffixes are properly stripped."""
    result = clean_version(input_version)
    assert result == expected


@pytest.mark.parametrize(
    "input_version,expected",
    [
        # Zero commits past tag - strip the suffix
        ("2.78.0+0.gabcdef", "2.78.0"),
        ("2.99.0+0.g1234567", "2.99.0"),
        ("2.78.0a1+0.gabcdef", "2.78.0a1"),
        # Zero commits with dirty - strip both
        ("2.78.0+0.gabcdef.dirty", "2.78.0"),
        ("2.99.0+0.g1234567.dirty", "2.99.0"),
    ],
)
def test_zero_distance_suffix_removed(input_version: str, expected: str) -> None:
    """Verify that +0.gXXXXXX suffixes are stripped when exactly on a tag."""
    result = clean_version(input_version)
    assert result == expected


@pytest.mark.parametrize(
    "input_version,expected",
    [
        # Non-zero commits past tag - keep the suffix (minus dirty)
        ("2.78.0+1.gabcdef", "2.78.0+1.gabcdef"),
        ("2.78.0+10.gabcdef", "2.78.0+10.gabcdef"),
        ("2.78.0+100.gabcdef", "2.78.0+100.gabcdef"),
        # Non-zero with dirty - keep distance, strip dirty
        ("2.78.0+1.gabcdef.dirty", "2.78.0+1.gabcdef"),
        ("2.78.0+10.gabcdef.dirty", "2.78.0+10.gabcdef"),
    ],
)
def test_non_zero_distance_preserved(input_version: str, expected: str) -> None:
    """Verify that non-zero distance suffixes are preserved (they indicate dev builds)."""
    result = clean_version(input_version)
    assert result == expected
