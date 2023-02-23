from fides.api.input_validation import InputStr, PhoneNumber


class TestInputStr:
    def test_html_sanitize(self) -> None:
        text_input = "<>&"
        expected = "something else"
        result = InputStr.validate(text_input)
        assert result == expected
