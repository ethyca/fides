from io import BytesIO
from zipfile import ZipFile

import pytest

from fides.api.common_exceptions import ValidationError
from fides.api.util.unsafe_file_util import verify_svg, verify_zip
from tests.ops.test_helpers.saas_test_utils import create_zip_file


class TestVerifySvg:
    def test_verify_svg(self):
        verify_svg(
            """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40"/>
            </svg>
            """
        )

    def test_verify_svg_no_laughing_allowed(self):
        """Test "billion laughs attack" is prevented"""
        with pytest.raises(ValidationError) as exc:
            verify_svg(
                """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <!DOCTYPE svg [
                <!ENTITY lol "lol">
                <!ELEMENT lolz (#PCDATA)>
                <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
                <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
                <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
                <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
                <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
                <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
                <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
                <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
                <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
                ]>
                <svg>
                    <lolz>&lol9;</lolz>
                </svg>
                """
            )
        assert "SVG file contains unsafe XML." in str(exc.value)

    def test_verify_svg_with_xlink(self):
        with pytest.raises(ValidationError) as exc:
            verify_svg(
                """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 100 100">
                    <circle id="circle" cx="50" cy="50" r="40"/>
                    <use xlink:href="#circle"/>
                </svg>
                """
            )
        assert "SVG files with xlink references are not allowed." in str(exc.value)


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
