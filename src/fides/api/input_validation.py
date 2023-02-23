"""Logic related to sanitizing and validating user application input."""
from html import escape
from re import compile as regex
from typing import Generator


class InputStr(str):
    """
    This class is designed to be used in place of the `str` type
    any place where user input is expected.

    The validation applied here does the typical sanitization/cleanup
    that is required when dealing with user-supplied input.
    """

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:

        # HTML Escapes
        value = escape(value)

        # Truncate to 100 characters
        value = value[:500]

        return value


class PhoneNumber(str):
    """Format validated type for phone numbers."""

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if value:
            pattern = regex(r"^\+[1-9]\d{1,14}$")
            if not pattern.search(value):
                raise ValueError(
                    "Identity phone number must be formatted in E.164 format. E.g +15558675309"
                )
        return value
