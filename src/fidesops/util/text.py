import re

import unidecode


def slugify(text: str) -> str:
    """
    Returns a URL compatible slug based upon the input text.
    """
    text = unidecode.unidecode(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text
