import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fides.api.ops.models.policy import ActionType, Policy
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fides.api.ops.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.ctl.core.config import get_config

CONFIG = get_config()
logger = logging.getLogger(__name__)


def build_required_privacy_request_kwargs(
    requested_at: Optional[datetime], policy_id: str
) -> Dict[str, Any]:
    """Build kwargs required for creating privacy request

    If identity verification is on, the request will have an initial status of
    "identity_unverified", otherwise, it will have an initial status of "pending".
    """
    status = (
        PrivacyRequestStatus.identity_unverified
        if CONFIG.execution.subject_identity_verification_required
        else PrivacyRequestStatus.pending
    )
    return {
        "requested_at": requested_at,
        "policy_id": policy_id,
        "status": status,
    }


def cache_data(
    privacy_request: PrivacyRequest,
    policy: Policy,
    identity: Identity,
    encryption_key: Optional[str],
    drp_request_body: Optional[DrpPrivacyRequestCreate],
) -> None:
    """Cache privacy request data"""
    # Store identity and encryption key in the cache
    logger.info("Caching identity for privacy request %s", privacy_request.id)
    privacy_request.cache_identity(identity)
    privacy_request.cache_encryption(encryption_key)  # handles None already

    # Store masking secrets in the cache
    logger.info("Caching masking secrets for privacy request %s", privacy_request.id)
    erasure_rules = policy.get_rules_for_action(action_type=ActionType.erasure)
    unique_masking_strategies_by_name: Set[str] = set()
    for rule in erasure_rules:
        strategy_name: str = rule.masking_strategy["strategy"]  # type: ignore
        configuration = rule.masking_strategy["configuration"]  # type: ignore
        if strategy_name in unique_masking_strategies_by_name:
            continue
        unique_masking_strategies_by_name.add(strategy_name)
        masking_strategy = MaskingStrategy.get_strategy(strategy_name, configuration)
        if masking_strategy.secrets_required():
            masking_secrets: List[
                MaskingSecretCache
            ] = masking_strategy.generate_secrets_for_cache()
            for masking_secret in masking_secrets:
                privacy_request.cache_masking_secret(masking_secret)
    if drp_request_body:
        privacy_request.cache_drp_request_body(drp_request_body)
