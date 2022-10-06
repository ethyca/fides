import re

import unidecode


def to_snake_case(text: str) -> str:
    """
    Returns a snake-cased str based upon the input text.
    E.g. "my example str" becomes "my_example_str"
    """
    text = unidecode.unidecode(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text
