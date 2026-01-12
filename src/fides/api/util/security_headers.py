import re
from dataclasses import dataclass

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fides.config import CONFIG

apply_recommended_headers = CONFIG.security.headers_mode == "recommended"


def is_exact_match(matcher: re.Pattern[str], path_name: str) -> bool:
    matched_content = re.fullmatch(matcher, path_name)
    return matched_content is not None


HeaderDefinition = tuple[str, str]


@dataclass
class HeaderRule:
    matcher: re.Pattern[str]
    headers: list[HeaderDefinition]


recommended_csp_header_value = re.sub(
    r"\s{2,}",
    " ",
    """
        default-src 'self';
        script-src 'self' 'unsafe-inline';
        style-src 'self' 'unsafe-inline';
        connect-src 'self';
        img-src 'self' blob: data:;
        font-src 'self';
        object-src 'none';
        base-uri 'self';
        form-action 'self';
        frame-ancestors 'self';
        upgrade-insecure-requests;
    """,
).strip()

recommended_headers: list[HeaderRule] = [
    HeaderRule(
        matcher=re.compile(r"/.*"),
        headers=[
            ("X-Content-Type-Options", "nosniff"),
            ("Strict-Transport-Security", "max-age=31536000"),
        ],
    ),
    HeaderRule(
        matcher=re.compile(r"^/((?!api|health).*)"),
        headers=[
            (
                "Content-Security-Policy",
                recommended_csp_header_value,
            ),
            ("X-Frame-Options", "SAMEORIGIN"),
        ],
    ),
]


def get_applicable_header_rules(
    path: str, header_rules: list[HeaderRule]
) -> list[HeaderDefinition]:
    header_names: set[str] = set()
    header_definitions: list[HeaderDefinition] = []

    for rule in header_rules:
        if is_exact_match(rule.matcher, path):
            for header in rule.headers:
                [header_name, _] = header
                if header_name not in header_names:
                    header_names.add(header_name)
                    header_definitions.append(header)

    return header_definitions


def apply_headers_to_response(
    headers: list[HeaderRule], request: Request, response: Response
) -> None:
    applicable_headers = get_applicable_header_rules(request.url.path, headers)
    for [header_name, header_value] in applicable_headers:
        response.headers.append(header_name, header_value)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Controls what security headers are included in Fides API responses
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore
        response = await call_next(request)

        if apply_recommended_headers:
            apply_headers_to_response(recommended_headers, request, response)

        return response
