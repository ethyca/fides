# pylint: disable=too-many-branches, too-many-statements
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from sqlalchemy.sql import column, or_, select
from sqlalchemy.sql.expression import nullslast

from fides.api.models.policy import Rule
from fides.api.models.privacy_request import (
    CustomPrivacyRequestField,
    PrivacyRequest,
    ProvidedIdentity,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    MAX_BULK_FILTER_RESULTS,
    PrivacyRequestBulkSelection,
    PrivacyRequestFilter,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.util.enums import ColumnSort
from fides.api.util.fuzzy_search_utils import get_decrypted_identities_automaton
from fides.api.util.text import normalize_location_code
from fides.config import CONFIG


def filter_privacy_request_queryset(
    db: Session,
    query: Query,
    filters: PrivacyRequestFilter,
    identity: Optional[str] = None,
    include_consent_webhook_requests: Optional[bool] = False,
) -> Query:
    """
    Utility method to apply filters to our privacy request query.

    Status supports "or" filtering:
    `status=["approved","pending"]` will be translated into an "or" query.

    The `identities` and `custom_privacy_request_fields` parameters allow
    searching for privacy requests that match any of the provided identities
    or custom privacy request fields, respectively. The filtering is performed
    using an "or" condition, meaning that a privacy request will be included
    in the results if it matches at least one of the provided identities or
    custom privacy request fields.
    """

    # Handle fuzzy search string
    if filters.fuzzy_search_str:
        if CONFIG.execution.fuzzy_search_enabled:
            decrypted_identities_automaton = get_decrypted_identities_automaton(db)

            # Set of associated privacy request ids
            fuzzy_search_identity_privacy_request_ids: Optional[set[str]] = set(
                x
                for list in decrypted_identities_automaton.values(
                    filters.fuzzy_search_str
                )
                for x in list
            )

            if not fuzzy_search_identity_privacy_request_ids:
                query = query.filter(
                    PrivacyRequest.id.ilike(f"{filters.fuzzy_search_str}%")
                )
            else:
                query = query.filter(
                    or_(
                        PrivacyRequest.id.in_(
                            fuzzy_search_identity_privacy_request_ids
                        ),
                        PrivacyRequest.id.ilike(f"{filters.fuzzy_search_str}%"),
                    )
                )
        else:
            # When fuzzy search is disabled, treat fuzzy_search_str as an
            # exact match on identity or partial match on privacy request ID
            identity_hashes = ProvidedIdentity.hash_value_for_search(
                filters.fuzzy_search_str
            )
            identity_set: set[str] = {
                identity[0]
                for identity in ProvidedIdentity.filter(
                    db=db,
                    conditions=(
                        (ProvidedIdentity.hashed_value.in_(identity_hashes))
                        & (ProvidedIdentity.privacy_request_id.isnot(None))
                    ),
                ).values(column("privacy_request_id"))
            }

            query = query.filter(
                or_(
                    PrivacyRequest.id.in_(identity_set),
                    PrivacyRequest.id.ilike(f"%{filters.fuzzy_search_str}%"),
                )
            )

    if identity:
        identity_hashes = ProvidedIdentity.hash_value_for_search(identity)
        identity_set: set[str] = {  # type: ignore[no-redef]
            identity[0]
            for identity in ProvidedIdentity.filter(
                db=db,
                conditions=(
                    (ProvidedIdentity.hashed_value.in_(identity_hashes))
                    & (ProvidedIdentity.privacy_request_id.isnot(None))
                ),
            ).values(column("privacy_request_id"))
        }
        query = query.filter(PrivacyRequest.id.in_(identity_set))

    if filters.identities:
        identity_conditions = [
            (ProvidedIdentity.field_name == field_name)
            & (
                ProvidedIdentity.hashed_value.in_(
                    ProvidedIdentity.hash_value_for_search(value)
                )
            )
            for field_name, value in filters.identities.items()
        ]

        identities_query = select([ProvidedIdentity.privacy_request_id]).where(
            or_(*identity_conditions)
            & (ProvidedIdentity.privacy_request_id.isnot(None))
        )
        query = query.filter(PrivacyRequest.id.in_(identities_query))

    if filters.custom_privacy_request_fields:
        # Note that if Custom Privacy Request Field values were arrays, they are not
        # indexed for searching and not discoverable here
        custom_field_conditions = [
            (CustomPrivacyRequestField.field_name == field_name)
            & (
                CustomPrivacyRequestField.hashed_value.in_(
                    CustomPrivacyRequestField.hash_value_for_search(value)
                )
            )
            for field_name, value in filters.custom_privacy_request_fields.items()
            if not isinstance(value, list)
        ]

        custom_fields_query = select(
            [CustomPrivacyRequestField.privacy_request_id]
        ).where(
            or_(*custom_field_conditions)
            & (CustomPrivacyRequestField.privacy_request_id.isnot(None))
        )
        query = query.filter(PrivacyRequest.id.in_(custom_fields_query))

    # Further restrict all PrivacyRequests by additional params
    if filters.request_id:
        query = query.filter(PrivacyRequest.id.ilike(f"%{filters.request_id}%"))
    if filters.external_id:
        query = query.filter(
            PrivacyRequest.external_id.ilike(f"{filters.external_id}%")
        )
    if filters.location:
        # Support filtering by exact location match or country prefix
        # e.g., "US" matches both "US" and "US-CA", "US-NY", etc.
        # "US-CA" matches only "US-CA"
        # Also normalize input to handle underscores and case insensitivity

        try:
            normalized_location = normalize_location_code(filters.location)
        except ValueError:
            # If normalization fails, treat as no results to prevent errors
            query = query.filter(False)
        else:
            if "-" in normalized_location:
                # Exact match for subdivision codes
                query = query.filter(PrivacyRequest.location == normalized_location)
            else:
                # Country code - match country or any subdivision of that country
                query = query.filter(
                    or_(
                        PrivacyRequest.location == normalized_location,
                        PrivacyRequest.location.ilike(f"{normalized_location}-%"),
                    )
                )
    if filters.status:
        query = query.filter(PrivacyRequest.status.in_(filters.status))
    if filters.created_lt:
        query = query.filter(PrivacyRequest.created_at < filters.created_lt)
    if filters.created_gt:
        query = query.filter(PrivacyRequest.created_at > filters.created_gt)
    if filters.started_lt:
        query = query.filter(PrivacyRequest.started_processing_at < filters.started_lt)
    if filters.started_gt:
        query = query.filter(PrivacyRequest.started_processing_at > filters.started_gt)
    if filters.completed_lt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.complete,
            PrivacyRequest.finished_processing_at < filters.completed_lt,
        )
    if filters.completed_gt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.complete,
            PrivacyRequest.finished_processing_at > filters.completed_gt,
        )
    if filters.errored_lt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.error,
            PrivacyRequest.finished_processing_at < filters.errored_lt,
        )
    if filters.errored_gt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.error,
            PrivacyRequest.finished_processing_at > filters.errored_gt,
        )
    if filters.action_type:
        action_type = filters.action_type
        if isinstance(action_type, ActionType):
            action_type = [action_type]
        policy_ids_for_action_type = (
            db.query(Rule)
            .filter(Rule.action_type.in_(action_type))
            .with_entities(Rule.policy_id)
            .distinct()
        )
        query = query.filter(PrivacyRequest.policy_id.in_(policy_ids_for_action_type))

    if not include_consent_webhook_requests:
        query = query.filter(
            or_(
                PrivacyRequest.source != PrivacyRequestSource.consent_webhook,
                PrivacyRequest.source.is_(None),
            )
        )

    # Filter out test privacy requests
    query = query.filter(
        or_(
            PrivacyRequest.source != PrivacyRequestSource.dataset_test,
            PrivacyRequest.source.is_(None),
        )
    )

    # Filter out deleted requests
    if not filters.include_deleted_requests:
        query = query.filter(PrivacyRequest.deleted_at.is_(None))

    return query


def sort_privacy_request_queryset(
    query: Query, sort_field: str, sort_direction: ColumnSort
) -> Query:
    """
    Sort the privacy request queryset by the given field and direction.
    """
    sort_object_attribute = getattr(PrivacyRequest, sort_field)
    sort_func = getattr(sort_object_attribute, sort_direction)
    return query.order_by(nullslast(sort_func()))


def resolve_request_ids_from_filters(
    db: Session,
    privacy_requests: PrivacyRequestBulkSelection,
) -> list[str]:
    """
    Resolve privacy request IDs from either explicit request_ids or filters.

    If request_ids is provided, use it directly.
    Otherwise, use filters to query for matching privacy requests and apply exclusions.

    Note: Pydantic validation ensures at least one of request_ids or filters is provided.

    Returns:
        List of privacy request IDs to act on (may be empty if no matches found)

    Raises:
        ValueError: If too many results are returned from filters (exceeds MAX_BULK_FILTER_RESULTS)
    """
    # If explicit request_ids are provided, use them directly
    if privacy_requests.request_ids:
        return privacy_requests.request_ids

    # Use filters to query for privacy requests
    # Note: Pydantic validator ensures filters is not None at this point
    filters = privacy_requests.filters
    assert filters is not None, "Filters must be provided when request_ids is not"

    query = PrivacyRequest.query_without_large_columns(db)
    query = filter_privacy_request_queryset(
        db=db,
        query=query,
        filters=filters,
    )

    # Apply exclusions if provided
    if privacy_requests.exclude_ids:
        query = query.filter(~PrivacyRequest.id.in_(privacy_requests.exclude_ids))

    # Only select IDs to avoid loading full objects
    # The service layer will handle batching if needed
    request_ids = [row[0] for row in query.with_entities(PrivacyRequest.id).all()]

    # Enforce the maximum limit for bulk filter results
    if len(request_ids) > MAX_BULK_FILTER_RESULTS:
        raise ValueError(
            f"Filter query returned {len(request_ids)} results, which exceeds the maximum of {MAX_BULK_FILTER_RESULTS}. Please narrow your filters."
        )

    return request_ids
