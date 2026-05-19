"""Access review hooks and shared filtering for the access package workflow.

Called from request_runner_service.py during the upload_access checkpoint.
Fidesplus registers callbacks via the dsr_report_builder_registry that
create the review row and check approval status.
"""

from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.graph import DatasetGraph
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.dsr_package.dsr_report_builder_registry import (
    get_review_approved_callback,
    is_access_review_required,
)
from fides.api.task.filter_results import filter_data_categories
from fides.api.util.collection_util import Row


def merge_storage_data(
    filtered_results: dict[str, list[dict[str, Optional[Any]]]],
    manual_data_for_storage: dict[str, list[dict[str, Optional[Any]]]],
    storage_attachments: list[dict[str, Any]] | None = None,
) -> None:
    """Merge manual data and attachments into filtered results for storage.

    Mutates filtered_results in place. Used by both the review path
    (build_filtered_results_for_storage) and the upload path
    (upload_and_save_access_results) to ensure consistent storage merging.
    """
    filtered_results.update(manual_data_for_storage)
    if storage_attachments:
        filtered_results["attachments"] = storage_attachments


def build_filtered_results_for_storage(
    policy: Policy,
    access_result: dict[str, list[Row]],
    dataset_graph: DatasetGraph,
    manual_data_for_storage: dict[str, list[dict[str, Optional[Any]]]],
    fides_connector_datasets: set[str],
    storage_attachments: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, list[dict[str, Optional[Any]]]]]:
    """Filter access results by each rule's target categories and merge storage data.

    Used by the review path to save filtered results for admin preview.
    """
    rule_filtered_results: dict[str, dict[str, list[dict[str, Optional[Any]]]]] = {}
    for rule in policy.get_rules_for_action(action_type=ActionType.access):
        target_categories: set[str] = {target.data_category for target in rule.targets}  # type: ignore[attr-defined]
        filtered_results: dict[str, list[dict[str, Optional[Any]]]] = (
            filter_data_categories(
                access_result,
                target_categories,
                dataset_graph,
                rule.key,
                fides_connector_datasets,
            )
        )
        merge_storage_data(
            filtered_results, manual_data_for_storage, storage_attachments
        )
        rule_filtered_results[rule.key] = filtered_results

    return rule_filtered_results


def should_wait_for_access_review(
    session: Session,
    policy: Policy,
    access_result: dict[str, list[Row]],
    dataset_graph: DatasetGraph,
    privacy_request: PrivacyRequest,
    manual_data_for_storage: dict[str, list[dict[str, Optional[Any]]]],
    fides_connector_datasets: set[str],
    storage_attachments: list[dict[str, Any]] | None = None,
) -> bool:
    """Check whether this request should pause for access package review.

    Returns True if the request was paused (caller should return/halt).
    Returns False if the request should continue to upload.
    """
    if not is_access_review_required():
        return False

    # Only gate requests that have access rules — pure erasure skips review
    if not policy.get_rules_for_action(action_type=ActionType.access):
        return False

    # Check if already approved (resume after approval)
    approved_callback = get_review_approved_callback()
    if approved_callback and approved_callback(privacy_request.id, session):
        return False

    # Save filtered results so the preview endpoint has data
    rule_filtered_results = build_filtered_results_for_storage(
        policy,
        access_result,
        dataset_graph,
        manual_data_for_storage,
        fides_connector_datasets,
        storage_attachments,
    )
    privacy_request.save_filtered_access_results(session, rule_filtered_results)

    privacy_request.status = PrivacyRequestStatus.awaiting_access_review
    privacy_request.save(db=session)
    logger.info(
        "Privacy request '{}' paused for access package review.",
        privacy_request.id,
    )
    return True
