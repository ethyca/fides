from io import BytesIO
from zipfile import ZipFile

import pytest

from fides.api.util.unsafe_file_util import verify_zip
from tests.ops.test_helpers.saas_test_utils import create_zip_file


class TestVerifyZip:
    @pytest.fixture
    def zip_file(self) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": "This file isn't that big, but it will be considered suspicious if the max file size is set too low",
            }
        )

    def test_verify_zip(self, zip_file):
        verify_zip(ZipFile(zip_file))

    def test_verify_zip_with_small_file_size_limit(self, zip_file):
        """We set the max file size to 1 byte, so the zip file should be rejected."""
        with pytest.raises(ValueError) as exc:
            verify_zip(ZipFile(zip_file), 1)
        assert "File size exceeds maximum allowed size" in str(exc.value)
