"""Shared helpers for PrivacyRequestService tests."""

from typing import Any, Optional
from unittest.mock import MagicMock

from fides.api.schemas.privacy_request import PrivacyRequestCreate
from fides.api.schemas.redis_cache import Identity
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService


def _make_action(custom_fields: Optional[dict[str, Any]]) -> MagicMock:
    a = MagicMock()
    a.custom_privacy_request_fields = custom_fields
    return a


def _svc() -> PrivacyRequestService:
    return PrivacyRequestService(MagicMock(), MagicMock(), MagicMock())


def _req(
    custom_fields: Optional[dict[str, Any]] = None, **kw: Any
) -> PrivacyRequestCreate:
    return PrivacyRequestCreate(
        identity=Identity(email="jane@example.com"),
        policy_key="default_access_policy",
        custom_privacy_request_fields=custom_fields,
        **kw,
    )
