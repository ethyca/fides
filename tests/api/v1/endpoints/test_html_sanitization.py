from src.fides.api.custom_types import validate_html_str


def test_html_sanitization_with_target_attribute():
    """Test that the validate_html_str function sanitizes the HTML string correctly, keeping the target attribute"""

    test_html = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank">privacy policy</a>'

    sanitized = validate_html_str(test_html)

    expected = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank" rel="noopener noreferrer">privacy policy</a>'

    assert sanitized == expected

def test_html_sanitization_with_hreflang_attribute():
    """Test that the validate_html_str function sanitizes the HTML string correctly, keeping the hreflang attribute"""

    test_html = 'See our <a href="https://www.somerandomwebsite.com/cookies/" hreflang="en" >privacy policy</a>'

    sanitized = validate_html_str(test_html)

    expected = 'See our <a href="https://www.somerandomwebsite.com/cookies/" hreflang="en" rel="noopener noreferrer">privacy policy</a>'

    assert sanitized == expected

def test_html_sanitization_blocks_event_handler_injections():
    """Test that the validate_html_str function blocks script injection"""

    test_html = 'See our <a href="https://www.somerandomwebsite.com/cookies/" onclick="alert(\'XSS\')">privacy policy</a>'

    sanitized = validate_html_str(test_html)

    expected = 'See our <a href="https://www.somerandomwebsite.com/cookies/" rel="noopener noreferrer">privacy policy</a>'

    assert sanitized == expected

def test_html_sanitization_blocks_script_tags_injections():
    """Test that the validate_html_str function blocks script tag injections"""

    test_html = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank"><script>alert("xss")</script>privacy policy</a> here.'

    sanitized = validate_html_str(test_html)

    expected = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank" rel="noopener noreferrer">privacy policy</a> here.'

    assert sanitized == expected

def test_html_sanitization_blocks_javascript_url_injections():
    """Test that the validate_html_str function blocks javascript url injections"""

    test_html = 'See our <a href="javascript:alert(\'XSS\')">privacy policy</a>'

    sanitized = validate_html_str(test_html)

    expected = 'See our <a rel="noopener noreferrer">privacy policy</a>'

    assert sanitized == expected

def test_html_sanitization_blocks_form_injections():
    """Test that the validate_html_str function blocks form injections"""

    test_html = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank">privacy policy</a><form action="https://www.amaliciouswebsite.com/hacking/" method="post"><input type="hidden" name="hackingstuff" value="somerandomvalue">'

    sanitized = validate_html_str(test_html)

    expected = 'See our <a href="https://www.somerandomwebsite.com/cookies/" target="_blank" rel="noopener noreferrer">privacy policy</a>'

    assert sanitized == expected

def test_html_sanitization_blocks_img_onalert_injections():
    """Test that the validate_html_str function blocks img onalert injections"""

    test_html = 'See our <img src=x:alert(alt) onerror=eval(src) alt=xss>Cookie policy'

    sanitized = validate_html_str(test_html)

    expected = 'See our Cookie policy'

    assert sanitized == expected

def test_html_sanitization_blocks_div_with_onclick_injection():
    """Test that the validate_html_str function blocks div with onclick injection"""

    test_html = 'See our <div onclick="alert(\'XSS\')">privacy policy</div>'

    sanitized = validate_html_str(test_html)

    expected = 'See our <div>privacy policy</div>'

    assert sanitized == expected
