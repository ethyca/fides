from unittest.mock import MagicMock, patch

import pytest

from fides.api.tasks.encryption_utils import encrypt_access_request_results


@pytest.fixture
def mock_cache():
    with patch(
        "fides.api.tasks.encryption_utils.get_dsr_cache_store"
    ) as mock_get_store:
        store = MagicMock()
        mock_get_store.return_value = store
        yield store


def test_encrypt_access_request_results_no_encryption_key(mock_cache):
    """Test that data is returned unencrypted when no encryption key is found in cache."""
    mock_cache.get_encryption.return_value = None
    test_data = "test_data"
    request_id = "test_request_id"

    result = encrypt_access_request_results(test_data, request_id)

    assert result == test_data
    mock_cache.get_encryption.assert_called_once_with("key")


def test_encrypt_access_request_results_with_encryption_key(mock_cache):
    """Test that data is encrypted when encryption key is found in cache."""
    # Use a 16-byte key (128 bits) for AES-GCM
    encryption_key = "0123456789abcdef"  # 16 bytes
    mock_cache.get_encryption.return_value = encryption_key
    test_data = "test_data"
    request_id = "test_request_id"

    result = encrypt_access_request_results(test_data, request_id)

    # The result should be a base64 encoded string containing the nonce and encrypted data
    assert isinstance(result, str)
    assert len(result) > 0
    mock_cache.get_encryption.assert_called_once_with("key")


def test_encrypt_access_request_results_with_bytes_input(mock_cache):
    """Test that bytes input is properly handled and encrypted."""
    encryption_key = "0123456789abcdef"  # 16 bytes
    mock_cache.get_encryption.return_value = encryption_key
    test_data = b"test_data"
    request_id = "test_request_id"

    result = encrypt_access_request_results(test_data, request_id)

    assert isinstance(result, str)
    assert len(result) > 0
    mock_cache.get_encryption.assert_called_once_with("key")


def test_encrypt_access_request_results_empty_data(mock_cache):
    """Test that empty data is handled correctly."""
    encryption_key = "0123456789abcdef"  # 16 bytes
    mock_cache.get_encryption.return_value = encryption_key
    test_data = ""
    request_id = "test_request_id"

    result = encrypt_access_request_results(test_data, request_id)

    assert isinstance(result, str)
    assert len(result) > 0
    mock_cache.get_encryption.assert_called_once_with("key")


def test_encrypt_access_request_results_special_characters(mock_cache):
    """Test that data with special characters is properly encrypted."""
    encryption_key = "0123456789abcdef"  # 16 bytes
    mock_cache.get_encryption.return_value = encryption_key
    test_data = "test_data!@#$%^&*()_+"
    request_id = "test_request_id"

    result = encrypt_access_request_results(test_data, request_id)

    assert isinstance(result, str)
    assert len(result) > 0
    mock_cache.get_encryption.assert_called_once_with("key")
