import pytest
from pydantic import BaseModel, ValidationError

from fides.api.schemas.language import SupportedLanguage, supported_languages_by_id


class TestLanguageSchema:
    def test_languages_by_id(self):
        # some basic language lookups
        assert supported_languages_by_id["ar"].name == "Arabic"
        assert supported_languages_by_id["en"].name == "English"
        assert supported_languages_by_id["es"].name == "Spanish"

        # norwegian is an edge case because `no` is a YAML keyword for False!
        assert supported_languages_by_id["no"].name == "Norwegian"

        # assert our language subtypes work
        assert supported_languages_by_id["pt-BR"].name == "Portuguese (Brazil)"
        assert supported_languages_by_id["pt-PT"].name == "Portuguese (Portugal)"
        assert supported_languages_by_id["sr-Cyrl"].name == "Serbian (Cyrillic)"
        assert supported_languages_by_id["sr-Latn"].name == "Serbian (Latin)"

    def test_language_enum(self):
        # some basic language lookups
        assert SupportedLanguage.arabic.value == "ar"
        assert SupportedLanguage.english.value == "en"
        assert SupportedLanguage.spanish.value == "es"

        # norwegian is an edge case because `no` is a YAML keyword for False!
        assert SupportedLanguage.norwegian.value == "no"

        # assert our language subtypes work
        assert SupportedLanguage.portuguese_brazil.value == "pt-BR"
        assert SupportedLanguage.portuguese_portugal.value == "pt-PT"
        assert SupportedLanguage.serbian_cyrillic.value == "sr-Cyrl"
        assert SupportedLanguage.serbian_latin.value == "sr-Latn"

    def test_language_enum_in_schema(self):
        class SamplePydanticSchema(BaseModel):
            test_prop: str
            language: SupportedLanguage

        test_schema_instance = SamplePydanticSchema(test_prop="foo", language="ar")
        assert test_schema_instance.language == SupportedLanguage.arabic

        test_schema_instance = SamplePydanticSchema(test_prop="foo", language="pt-BR")
        assert test_schema_instance.language == SupportedLanguage.portuguese_brazil

        # test that specifying an invalid language (e.g. es-MX) throws a validation error
        with pytest.raises(ValidationError):
            test_schema_instance = SamplePydanticSchema(
                test_prop="foo", language="es-MX"
            )
