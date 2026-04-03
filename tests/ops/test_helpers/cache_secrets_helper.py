from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.util.cache import (
    FidesopsRedis,
    get_cache,
    get_dsr_cache_store,
    get_masking_secret_cache_key,
)


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
    """Testing helper that removes cached identities from the Privacy Request.

    Some of our Privacy Request fixtures automatically cache identities -
    this clears them using the DSR cache store. The get_cached_identity_data
    call migrates any legacy keys before deletion.
    """
    store = get_dsr_cache_store(request_id)
    # get_cached_identity_data triggers migration (legacy → new), so all
    # identity keys will be in new format after this call.
    identity_data = store.get_cached_identity_data()
    for attr in identity_data:
        store.delete(f"identity:{attr}")
