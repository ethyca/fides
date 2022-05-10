import logging
from datetime import datetime
from typing import Optional, Any, Dict, Set, List

from fidesops.models.policy import Policy, ActionType
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fidesops.schemas.masking.masking_configuration import MaskingConfiguration
from fidesops.schemas.masking.masking_secrets import MaskingSecretCache
from fidesops.schemas.policy import Rule
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.service.masking.strategy.masking_strategy_factory import get_strategy

logger = logging.getLogger(__name__)


def build_required_privacy_request_kwargs(
    requested_at: Optional[datetime], policy_id: str
) -> Dict[str, Any]:
    """Build kwargs required for creating privacy request"""
    return {
        "requested_at": requested_at,
        "policy_id": policy_id,
        "status": "pending",
    }


def cache_data(
    privacy_request: PrivacyRequest,
    policy: Policy,
    identity: PrivacyRequestIdentity,
    encryption_key: Optional[str],
    drp_request_body: Optional[DrpPrivacyRequestCreate],
) -> None:
    """Cache privacy request data"""
    # Store identity and encryption key in the cache
    logger.info(f"Caching identity for privacy request {privacy_request.id}")
    privacy_request.cache_identity(identity)
    privacy_request.cache_encryption(encryption_key)  # handles None already

    # Store masking secrets in the cache
    logger.info(f"Caching masking secrets for privacy request {privacy_request.id}")
    erasure_rules: List[Rule] = policy.get_rules_for_action(
        action_type=ActionType.erasure
    )
    unique_masking_strategies_by_name: Set[str] = set()
    for rule in erasure_rules:
        strategy_name: str = rule.masking_strategy["strategy"]
        configuration: MaskingConfiguration = rule.masking_strategy["configuration"]
        if strategy_name in unique_masking_strategies_by_name:
            continue
        unique_masking_strategies_by_name.add(strategy_name)
        masking_strategy = get_strategy(strategy_name, configuration)
        if masking_strategy.secrets_required():
            masking_secrets: List[
                MaskingSecretCache
            ] = masking_strategy.generate_secrets_for_cache()
            for masking_secret in masking_secrets:
                privacy_request.cache_masking_secret(masking_secret)
    if drp_request_body:
        privacy_request.cache_drp_request_body(drp_request_body)
