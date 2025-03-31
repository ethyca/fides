from src.fides.api.custom_types import validate_html_str


def test_html_sanitization():
    """Test that the validate_html_str function sanitizes the HTML string correctly, keeping the target attribute"""

    test_html = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank">privacy policy</a>'

    sanitized = validate_html_str(test_html)

    expected = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank" rel="noopener noreferrer">privacy policy</a>'

    assert sanitized == expected
