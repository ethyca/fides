import re

import unidecode


def to_snake_case(text: str) -> str:
    """
    Returns a snake-cased str based upon the input text.

    Examples:
        "foo bar" -> "foo_bar"
        "foo\nbar" -> "foo_bar"
        "foo\tbar" -> "foo_bar"
        "foo-bar" -> "foo_bar"
        "foo*bar" -> "foobar"
    """
    text = unidecode.unidecode(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text
