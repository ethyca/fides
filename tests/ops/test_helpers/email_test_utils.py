"""Shared utilities for testing email content and templates."""

import re
from urllib.parse import urlparse


def extract_urls_from_html(html_content: str) -> list[str]:
    """
    Extract URLs from HTML content using regex.

    Handles both href attributes and plain text URLs.

    Args:
        html_content: The HTML content to extract URLs from

    Returns:
        List of unique URLs found in the content
    """
    urls = []

    # Pattern to match URLs in href attributes
    href_pattern = r'href=["\']([^"\']*)["\']'
    href_matches = re.findall(href_pattern, html_content)
    for url in href_matches:
        if url and url.startswith("http"):
            urls.append(url)

    # Pattern to match plain text URLs (not in attributes)
    url_pattern = r'https?://[^\s<>"\']+'
    url_matches = re.findall(url_pattern, html_content)
    for url in url_matches:
        if url not in urls:  # Avoid duplicates
            urls.append(url)

    return urls


def assert_url_hostname_present(html_content: str, expected_hostname: str) -> None:
    """
    Assert that at least one URL in the HTML content has the expected hostname.

    This is more robust than simple substring matching as it properly parses
    URLs and validates the hostname component specifically, handling cases where
    URLs may be HTML-escaped or contain query parameters.

    Args:
        html_content: The HTML content to search for URLs
        expected_hostname: The hostname to look for (e.g., "privacy.example.com")

    Raises:
        AssertionError: If no URL with the expected hostname is found
    """
    urls = extract_urls_from_html(html_content)

    found_hostnames = []
    for url in urls:
        try:
            parsed_url = urlparse(url)
            found_hostnames.append(parsed_url.hostname)
            if parsed_url.hostname == expected_hostname:
                return  # Found the expected hostname
        except Exception:
            continue  # Skip malformed URLs

    # If we get here, the expected hostname was not found
    raise AssertionError(
        f"Expected hostname '{expected_hostname}' not found in any URLs. "
        f"Found URLs: {urls}, Found hostnames: {found_hostnames}"
    )


def assert_html_contains_url_with_hostname(
    html_content: str, expected_hostname: str
) -> None:
    """
    Alias for assert_url_hostname_present for consistency with other HTML assertion helpers.

    Args:
        html_content: The HTML content to search for URLs
        expected_hostname: The hostname to look for (e.g., "privacy.example.com")

    Raises:
        AssertionError: If no URL with the expected hostname is found
    """
    assert_url_hostname_present(html_content, expected_hostname)
