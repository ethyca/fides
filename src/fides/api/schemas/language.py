from enum import Enum
from os.path import dirname, join
from typing import Dict

import yaml
from pydantic import BaseModel

from fides.api.util.text import to_snake_case
from fides.config.helpers import load_file

LANGUAGES_YAML_FILE_PATH = join(
    dirname(__file__),
    "../../data",
    "language",
    "languages.yml",
)


class Language(BaseModel):
    id: str
    name: str


def _load_supported_languages() -> Dict[str, Language]:
    """Loads language dict based on yml file on disk"""
    with open(load_file([LANGUAGES_YAML_FILE_PATH]), "r", encoding="utf-8") as file:
        _languages = yaml.safe_load(file).get("languages", [])
        language_dict = {}
        for language in _languages:
            language_dict[language["id"]] = Language.parse_obj(language)
        return language_dict


supported_languages_by_id: Dict[str, Language] = (
    _load_supported_languages()
)  # should only be accessed for read-only access


# dynamically create an enum based on definitions loaded from YAML
SupportedLanguage: Enum = Enum(  # type: ignore[misc]
    "SupportedLanguage",
    {
        to_snake_case(language.name): language.id
        for language in supported_languages_by_id.values()
    },
)
