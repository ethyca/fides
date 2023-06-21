"""Logic related to sanitizing and validating user application input."""
from html import escape
from re import compile as regex
from typing import Generator


class SafeStr(str):
    """
    This class is designed to be used in place of the `str` type
    any place where user input is expected.

    The validation applied here does the typical sanitization/cleanup
    that is required when dealing with user-supplied input.
    """

    @classmethod
    def __get_validators__(cls) -> Generator:  # pragma: no cover
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        # HTML Escapes
        value = escape(value)

        if len(value) > 32000:
            raise ValueError("Value must be 32000 characters or less.")

        return value


class PhoneNumber(str):
    """
    Format validated type for phone numbers.

    Standard format can be found here: https://en.wikipedia.org/wiki/E.164
    """

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        # The front-end sends an empty string if the user doesn't input anything
        if value == "":
            return ""
        max_length = 16  # Includes the +
        min_length = 9
        pattern = regex(r"^\+[1-9]\d{1,14}$")
        if (
            len(value) > max_length
            or len(value) < min_length
            or not pattern.search(value)
        ):
            raise ValueError(
                "Phone number must be formatted in E.164 format, i.e. '+15558675309'."
            )
        return value
