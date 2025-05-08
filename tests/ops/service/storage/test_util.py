from typing import Optional

import pytest
from pytest import param

from fides.api.service.storage.util import (
    AllowedFileType,
    get_allowed_file_type_or_raise,
)


@pytest.mark.parametrize(
    "file_key, expected_file_type",
    [
        param("test.pdf", AllowedFileType.pdf.value, id="pdf"),
        param("test.docx", AllowedFileType.docx.value, id="docx"),
        param("test.txt", AllowedFileType.txt.value, id="txt"),
        param(
            "test.not_a_file_type.txt",
            AllowedFileType.txt.value,
            id="not_a_file_type_dot_txt",
        ),
        param(
            "test.not_a_file_type.txt.pdf",
            AllowedFileType.pdf.value,
            id="not_a_file_type_dot_txt_dot_pdf",
        ),
        param("test.yaml", None, id="yaml"),
        param("test", None, id="no_extension"),
        param("test.", None, id="no_extension_dot"),
        param("test.not_a_file_type", None, id="not_a_file_type"),
    ],
)
def test_get_file_type(file_key: str, expected_file_type: Optional[str]):
    """Test that the get_file_type function returns the correct file type"""
    if expected_file_type is None:
        with pytest.raises(ValueError) as excinfo:
            get_allowed_file_type_or_raise(file_key)
            assert "Invalid or unallowed file extension" in str(excinfo.value)
    else:
        assert get_allowed_file_type_or_raise(file_key) == expected_file_type
