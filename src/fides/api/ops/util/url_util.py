from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit


def set_query_parameter(url: str, param_name: str, param_value: str) -> str:
    """Given a URL, set or replace a query parameter and return the
    modified URL.

    'http://example.com?foo=stuff&biz=baz'
    """

    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)

    query_params[param_name] = [param_value]
    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))
