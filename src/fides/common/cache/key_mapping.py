"""
Key mapping: legacy Redis key patterns to the DSR store key format.

Maps (dsr_id, field_type, field_key, ...) to:
- new_key: dsr:{dsr_id}:{part}  (part = field_type:field_key or field_type)
- legacy_key: the key used by the old cache API (for encoded objects, the
  logical key; set_encoded_object stores under EN_ + logical key in Redis).
"""

from typing import Tuple

# TODO: Move to dsr_store.py when deprecating
# Once we don't need to do migrations we can get rid of this file,
# the prefix should move to the dsr_store.py (not there to avoid circular
# dependencies since the store depends on this)
DSR_KEY_PREFIX = "dsr:"


def _new_key(dsr_id: str, part: str) -> str:
    """Build the new-format Redis key."""
    return f"{DSR_KEY_PREFIX}{dsr_id}:{part}"


def _part(field_type: str, field_key: str = "") -> str:
    """Build the part string (field_type or field_type:field_key)."""
    return f"{field_type}:{field_key}" if field_key else field_type


class KeyMapper:
    """
    Maps DSR cache field types to new keys and legacy keys.
    All patterns discovered in the privacy request cache audit are encoded here.
    """

    # --- Simple key-value (legacy = Redis key as used with set_with_autoexpire / get) ---

    @staticmethod
    def identity(dsr_id: str, attr: str) -> Tuple[str, str]:
        """New: dsr:{id}:identity:{attr}. Legacy: id-{id}-identity-{attr}."""
        part = _part("identity", attr)
        return _new_key(dsr_id, part), f"id-{dsr_id}-identity-{attr}"

    @staticmethod
    def custom_field(dsr_id: str, field_key: str) -> Tuple[str, str]:
        """New: dsr:{id}:custom_field:{key}. Legacy: id-{id}-custom-privacy-request-field-{key}."""
        part = _part("custom_field", field_key)
        return _new_key(
            dsr_id, part
        ), f"id-{dsr_id}-custom-privacy-request-field-{field_key}"

    @staticmethod
    def drp(dsr_id: str, attr: str) -> Tuple[str, str]:
        """New: dsr:{id}:drp:{attr}. Legacy: id-{id}-drp-{attr}."""
        part = _part("drp", attr)
        return _new_key(dsr_id, part), f"id-{dsr_id}-drp-{attr}"

    @staticmethod
    def encryption(dsr_id: str, attr: str) -> Tuple[str, str]:
        """New: dsr:{id}:encryption:{attr}. Legacy: id-{id}-encryption-{attr}."""
        part = _part("encryption", attr)
        return _new_key(dsr_id, part), f"id-{dsr_id}-encryption-{attr}"

    @staticmethod
    def masking_secret(dsr_id: str, strategy: str, secret_type: str) -> Tuple[str, str]:
        """New: dsr:{id}:masking_secret:{strategy}:{secret_type}. Legacy: id-{id}-masking-secret-{strategy}-{secret_type}."""
        part = f"masking_secret:{strategy}:{secret_type}"
        return _new_key(
            dsr_id, part
        ), f"id-{dsr_id}-masking-secret-{strategy}-{secret_type}"

    @staticmethod
    def async_execution(dsr_id: str) -> Tuple[str, str]:
        """New: dsr:{id}:async_execution. Legacy: id-{id}-async-execution."""
        part = "async_execution"
        return _new_key(dsr_id, part), f"id-{dsr_id}-async-execution"

    @staticmethod
    def retry_count(dsr_id: str) -> Tuple[str, str]:
        """New: dsr:{id}:retry_count. Legacy: id-{id}-privacy-request-retry-count."""
        part = "retry_count"
        return _new_key(dsr_id, part), f"id-{dsr_id}-privacy-request-retry-count"

    # --- Encoded objects (legacy = logical key; Redis stores EN_ + logical) ---

    @staticmethod
    def webhook_manual_access(dsr_id: str, webhook_id: str) -> Tuple[str, str]:
        """New: dsr:{id}:webhook_manual_access:{webhook_id}. Legacy logical: WEBHOOK_MANUAL_ACCESS_INPUT__{id}__{webhook_id}."""
        part = _part("webhook_manual_access", webhook_id)
        return _new_key(
            dsr_id, part
        ), f"WEBHOOK_MANUAL_ACCESS_INPUT__{dsr_id}__{webhook_id}"

    @staticmethod
    def webhook_manual_erasure(dsr_id: str, webhook_id: str) -> Tuple[str, str]:
        """New: dsr:{id}:webhook_manual_erasure:{webhook_id}. Legacy logical: WEBHOOK_MANUAL_ERASURE_INPUT__{id}__{webhook_id}."""
        part = _part("webhook_manual_erasure", webhook_id)
        return _new_key(
            dsr_id, part
        ), f"WEBHOOK_MANUAL_ERASURE_INPUT__{dsr_id}__{webhook_id}"

    @staticmethod
    def data_use_map(dsr_id: str) -> Tuple[str, str]:
        """New: dsr:{id}:data_use_map. Legacy logical: DATA_USE_MAP__{id}."""
        part = "data_use_map"
        return _new_key(dsr_id, part), f"DATA_USE_MAP__{dsr_id}"

    @staticmethod
    def email_info(
        dsr_id: str, step: str, dataset: str, collection: str
    ) -> Tuple[str, str]:
        """New: dsr:{id}:email_info:{step}:{dataset}:{collection}. Legacy logical: EMAIL_INFORMATION__{id}__{step}__{dataset}__{collection}."""
        part = f"email_info:{step}:{dataset}:{collection}"
        return _new_key(
            dsr_id, part
        ), f"EMAIL_INFORMATION__{dsr_id}__{step}__{dataset}__{collection}"

    @staticmethod
    def paused_location(dsr_id: str) -> Tuple[str, str]:
        """New: dsr:{id}:paused_location. Legacy logical: PAUSED_LOCATION__{id}."""
        part = "paused_location"
        return _new_key(dsr_id, part), f"PAUSED_LOCATION__{dsr_id}"

    @staticmethod
    def failed_location(dsr_id: str) -> Tuple[str, str]:
        """New: dsr:{id}:failed_location. Legacy logical: FAILED_LOCATION__{id}."""
        part = "failed_location"
        return _new_key(dsr_id, part), f"FAILED_LOCATION__{dsr_id}"

    @staticmethod
    def access_request(dsr_id: str, key: str) -> Tuple[str, str]:
        """New: dsr:{id}:access_request:{key}. Legacy logical: {id}__{key} (key e.g. access_request__dataset:collection)."""
        part = _part("access_request", key)
        return _new_key(dsr_id, part), f"{dsr_id}__{key}"

    @staticmethod
    def erasure_request(dsr_id: str, key: str) -> Tuple[str, str]:
        """New: dsr:{id}:erasure_request:{key}. Legacy logical: {id}__erasure_request__{key}."""
        part = _part("erasure_request", key)
        return _new_key(dsr_id, part), f"{dsr_id}__erasure_request__{key}"

    @staticmethod
    def placeholder_results(dsr_id: str, key: str) -> Tuple[str, str]:
        """New: dsr:{id}:placeholder_results:{key}. Legacy logical: PLACEHOLDER_RESULTS__{id}__{key}."""
        part = _part("placeholder_results", key)
        return _new_key(dsr_id, part), f"PLACEHOLDER_RESULTS__{dsr_id}__{key}"

    # --- Index prefix (for get_all_keys / clear) ---

    @staticmethod
    def index_prefix(dsr_id: str) -> str:
        """Index set key prefix for this DSR: __idx:dsr:{id}."""
        return f"__idx:{DSR_KEY_PREFIX}{dsr_id}"
