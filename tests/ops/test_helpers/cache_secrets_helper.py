from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.util.cache import FidesopsRedis, get_cache, get_masking_secret_cache_key


def cache_secret(masking_secret_cache: MaskingSecretCache, request_id: str) -> None:
    cache: FidesopsRedis = get_cache()
    cache.set_with_autoexpire(
        get_masking_secret_cache_key(
            request_id,
            masking_strategy=masking_secret_cache.masking_strategy,
            secret_type=masking_secret_cache.secret_type,
        ),
        FidesopsRedis.encode_obj(masking_secret_cache.secret),
    )


def clear_cache_secrets(request_id: str) -> None:
    cache: FidesopsRedis = get_cache()
    cache.delete_keys_by_prefix(f"id-{request_id}-masking-secret)")


def clear_cache_identities(request_id: str) -> None:
    """Testing helper just removes some cached identities from the Privacy Request for testing.

    Some of our Privacy Request fixtures automatically cache identities -
    this clears them using the DSR cache store. Handles both new and legacy key formats.
    """
    from fides.api.util.cache import get_cache, get_dsr_cache_store, get_identity_cache_key

    cache: FidesopsRedis = get_cache()
    
    # First, try to get identity data which will migrate any legacy keys
    with get_dsr_cache_store() as store:
        identity_data = store.get_cached_identity_data(request_id)
        # Delete all identity attributes found
        for attr in identity_data.keys():
            store.delete(request_id, f"identity:{attr}")
        
        # Also scan for any remaining legacy identity keys and delete them
        legacy_keys = cache.get_keys_by_prefix(f"id-{request_id}-identity-")
        for legacy_key in legacy_keys:
            # Extract attribute name and delete via store
            attr = legacy_key.split("-")[-1]
            store.delete(request_id, f"identity:{attr}")
