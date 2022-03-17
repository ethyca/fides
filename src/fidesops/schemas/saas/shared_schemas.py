from typing import Any, Dict, Literal, Optional, Tuple


SaaSRequestParams = Tuple[Literal["GET", "PUT"], str, Dict[str, Any], Optional[str]]
"""Custom type to represent a tuple of HTTP method, path, params, and body values for a SaaS request"""
