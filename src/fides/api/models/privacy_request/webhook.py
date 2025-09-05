# pylint: disable=R0401, C0302

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum as EnumType
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from fides.api.models.policy import PolicyPreWebhook, WebhookDirection
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.oauth.jwt import generate_jwe
from fides.api.schemas.external_https import (
    DownloadTokenJWE,
    RequestTaskJWE,
    WebhookJWE,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_READ_ACCESS_RESULTS,
    PRIVACY_REQUEST_REVIEW,
)
from fides.config import CONFIG


class CallbackType(EnumType):
    """We currently have three types of Webhooks: pre-approval, pre (-execution), post (-execution)"""

    pre_approval = "pre_approval"
    pre = "pre"  # pre-execution
    post = "post"  # post-execution


class SecondPartyRequestFormat(BaseModel):
    """
    The request body we will use when calling a user's HTTP endpoint from fides.api
    This class is defined here to avoid circular import issues between this file and
    models.policy
    """

    privacy_request_id: str
    privacy_request_status: PrivacyRequestStatus
    direction: WebhookDirection
    callback_type: CallbackType
    identity: Identity
    policy_action: Optional[ActionType] = None
    model_config = ConfigDict(use_enum_values=True)
    privacy_request: Dict[str, Any]
    timestamp: datetime


def generate_request_callback_resume_jwe(webhook: PolicyPreWebhook) -> str:
    """
    Generate a JWE to be used to resume privacy request execution.
    """
    jwe = WebhookJWE(
        webhook_id=webhook.id,
        scopes=[PRIVACY_REQUEST_CALLBACK_RESUME],
        iat=datetime.now().isoformat(),
    )
    return generate_jwe(
        json.dumps(jwe.model_dump(mode="json")),
        CONFIG.security.app_encryption_key,
    )


def generate_request_callback_pre_approval_jwe(webhook: PreApprovalWebhook) -> str:
    """
    Generate a JWE to be used to mark privacy requests as eligible / not-eligible for pre approval.
    """
    jwe = WebhookJWE(
        webhook_id=webhook.id,
        scopes=[PRIVACY_REQUEST_REVIEW],
        iat=datetime.now().isoformat(),
    )
    return generate_jwe(
        json.dumps(jwe.model_dump(mode="json")),
        CONFIG.security.app_encryption_key,
    )


def generate_request_task_callback_jwe(request_task: RequestTask) -> str:
    """
    Generate a JWE to be used to resume privacy request execution when a
    callback endpoint is hit for a RequestTask
    """
    jwe = RequestTaskJWE(
        request_task_id=request_task.id,
        scopes=[PRIVACY_REQUEST_CALLBACK_RESUME],
        iat=datetime.now().isoformat(),
    )
    return generate_jwe(
        json.dumps(jwe.model_dump(mode="json")),
        CONFIG.security.app_encryption_key,
    )


def generate_privacy_request_download_token(privacy_request_id: str) -> str:
    """
    Generate a JWE token for users to download their privacy request access package.
    This is currently used for the DSR package link endpoint which provides a redirect
    to a presigned URL for the access results.
    This token expires based on the configured TTL for security.
    """
    from datetime import timedelta

    now = datetime.now()
    # Use the configured TTL from security settings
    expiration = now + timedelta(
        seconds=CONFIG.security.subject_request_download_link_ttl_seconds
    )

    jwe = DownloadTokenJWE(
        privacy_request_id=privacy_request_id,
        scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS],
        iat=now.isoformat(),
        exp=expiration.isoformat(),
    )
    return generate_jwe(
        json.dumps(jwe.model_dump(mode="json")),
        CONFIG.security.app_encryption_key,
    )
