# pylint: disable=no-name-in-module
"""Logic related to sanitizing and validating user application input."""
from html import escape
from re import compile as regex
from typing import Annotated

from nh3 import clean
from pydantic import AfterValidator, AnyHttpUrl, AnyUrl, BeforeValidator

from fides.api.util.unsafe_file_util import verify_css


def validate_safe_str(val: str) -> str:
    """
    Validator for SafeStr that is designed to be used in place of the `str` type
    any place where user input is expected.

    The validation applied here does the typical sanitization/cleanup
    that is required when dealing with user-supplied input.
    """
    # HTML Escapes
    value = escape(val)

    if len(value) > 32000:
        raise ValueError("Value must be 32000 characters or less.")

    return value


SafeStr = Annotated[str, BeforeValidator(validate_safe_str)]


def validate_html_str(val: str) -> str:
    """
    Validator function for HTMLStr - designed to be used in place of the `str` type
    any place where user inputted HTML text is expected.

    The validation applied here enforces that only a subset of "safe" HTML is
    supported to prevent XSS or similar attacks.

    """
    # Assert text doesn't include an complex/malicious HTML.
    # Allow only basic markup tags, for extra safety
    ALLOWED_HTML_TAGS = {
        "a",
        "blockquote",
        "br",
        "div",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "i",
        "li",
        "ol",
        "p",
        "pre",
        "q",
        "rt",
        "ruby",
        "s",
        "span",
        "strong",
        "u",
    }
    if val:
        return clean(val, tags=ALLOWED_HTML_TAGS)
    return val


HtmlStr = Annotated[str, BeforeValidator(validate_html_str)]


def validate_phone_number(value: str) -> str:
    """Validator for PhoneNumber

    Standard format can be found here: https://en.wikipedia.org/wiki/E.164
    """
    # The front-end sends an empty string if the user doesn't input anything
    if value == "":
        return ""
    max_length = 16  # Includes the +
    min_length = 9
    pattern = regex(r"^\+[1-9]\d{1,14}$")
    if len(value) > max_length or len(value) < min_length or not pattern.search(value):
        raise ValueError(
            "Phone number must be formatted in E.164 format, i.e. '+15558675309'."
        )
    return value


PhoneNumber = Annotated[str, BeforeValidator(validate_phone_number)]


def validate_gpp_mechanism_consent_value(value: str) -> str:
    """
    Validator for GPPMechanismConsentValue -  Allowable consent values for GPP Mechanism Mappings.
    """
    pattern = regex(r"^\d+$")
    if not isinstance(value, str) or not pattern.search(value):
        raise ValueError("GPP Mechanism consent value must be a string of digits.")
    return value


GPPMechanismConsentValue = Annotated[
    str, BeforeValidator(validate_gpp_mechanism_consent_value)
]


def validate_path_of_url(value: AnyUrl) -> str:
    """
    A URL origin value. See https://developer.mozilla.org/en-US/docs/Glossary/Origin.

    We perform the basic URL validation, but also prevent URLs with paths,
    as paths are not part of an origin.
    """
    if value.path and value.path != "/":
        raise ValueError("URL origin values cannot contain a path.")

    # Intentionally serializing as a string instead of a URL.
    # Intentionally removing trailing slash. In Pydantic V2 AnyURL will add a trailing slash to root URL's so stripping this off.
    return str(value).rstrip("/")


URLOriginString = Annotated[AnyUrl, AfterValidator(validate_path_of_url)]


def validate_css_str(value: str) -> str:
    """
    Validator for CssStr

    A custom string type that represents a valid CSS stylesheet.

    The `CssStr` type automatically validates the input value using the `verify_css` function
    to ensure that it is a valid CSS stylesheet. The validation checks for parsing errors,
    import statements, and calls to the url() function.

    If the input value is not a string or fails the CSS validation, a `ValidationError` is raised.
    """
    if not isinstance(value, str):
        raise TypeError("CssStr must be a string")
    verify_css(value)
    return value


CssStr = Annotated[str, BeforeValidator(validate_css_str)]


def validate_path_of_http_url_no_slash(value: AnyHttpUrl) -> str:
    """Converts an AnyHttpUrl to a string and strips trailing slash"""
    return str(value).rstrip("/")


AnyHttpUrlStringRemovesSlash = Annotated[
    AnyHttpUrl, AfterValidator(validate_path_of_http_url_no_slash)
]
