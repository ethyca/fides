from typing import Optional

import pytest
from pytest import param

from fides.api.service.storage.util import get_allowed_file_type_or_raise


@pytest.mark.parametrize(
    "file_key, expected_file_type",
    [
        param("test.pdf", "pdf", id="pdf"),
        param("test.docx", "docx", id="docx"),
        param("test.txt", "txt", id="txt"),
        param("test", None, id="no_extension"),
        param("test.", None, id="no_extension_dot"),
        param("test.not_a_file_type", None, id="not_a_file_type"),
    ],
)
def test_get_file_type(file_key: str, expected_file_type: Optional[str]):
    """Test that the get_file_type function returns the correct file type"""
    if expected_file_type is None and "." in file_key:
        with pytest.raises(ValueError):
            get_allowed_file_type_or_raise(file_key)
    else:
        assert get_allowed_file_type_or_raise(file_key) == expected_file_type
