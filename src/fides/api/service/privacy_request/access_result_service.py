import time
from copy import deepcopy
from typing import Any, Optional

import sqlalchemy.exc
from loguru import logger

# pylint: disable=no-name-in-module
from psycopg2.errors import InternalError_  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from fides.api import common_exceptions
from fides.api.graph.graph import DatasetGraph
from fides.api.models.attachment import AttachmentReferenceType
from fides.api.models.policy import Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.attachment_handling import (
    get_attachments_content,
    process_attachments_for_upload,
)
from fides.api.service.privacy_request.manual_webhook_service import (
    ManualWebhookResults,
)
from fides.api.service.storage.storage_uploader_service import upload
from fides.api.task.filter_results import filter_data_categories
from fides.api.util.collection_util import Row
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context


@log_context(capture_args={"privacy_request_id": LoggerContextKeys.privacy_request_id})
def upload_access_results(
    session: Session,
    policy: Policy,
    rule: Rule,
    results_to_upload: dict[str, list[dict[str, Optional[Any]]]],
    dataset_graph: DatasetGraph,
    privacy_request: PrivacyRequest,
    upload_attachments: list[dict[str, Any]],
) -> list[str]:
    """Upload results for a single rule and return download URLs and modified results."""
    start_time = time.time()
    download_urls: list[str] = []
    storage_destination = rule.get_storage_destination(session)

    if upload_attachments:
        results_to_upload["attachments"] = upload_attachments

    logger.info("Starting access request upload for rule {}", rule.key)
    try:
        download_url: Optional[str] = upload(
            db=session,
            privacy_request=privacy_request,
            data=results_to_upload,
            storage_key=storage_destination.key,  # type: ignore
            data_category_field_mapping=dataset_graph.data_category_field_mapping,
            data_use_map=privacy_request.get_cached_data_use_map(),
        )
        if download_url:
            download_urls.append(download_url)
            logger.bind(
                time_taken=time.time() - start_time,
            ).info("Access package upload successful for privacy request.")
            privacy_request.add_success_execution_log(
                session,
                connection_key=None,
                dataset_name="Access package upload",
                collection_name=None,
                message="Access package upload successful for privacy request.",
                action_type=ActionType.access,
            )
    except common_exceptions.StorageUploadError as exc:
        logger.error(
            "Error uploading subject access data for rule {} on policy {}: {}",
            rule.key,
            policy.key,
            str(exc),
        )
        privacy_request.add_error_execution_log(
            session,
            connection_key=None,
            dataset_name="Access package upload",
            collection_name=None,
            message=f"Access package upload failed for privacy request: {str(exc)}",
            action_type=ActionType.access,
        )
        privacy_request.status = PrivacyRequestStatus.error

    return download_urls


@log_context(
    capture_args={
        "privacy_request_id": LoggerContextKeys.privacy_request_id,
    }
)
def save_access_results(
    session: Session,
    privacy_request: PrivacyRequest,
    download_urls: list[str],
    rule_filtered_results: dict[str, dict[str, list[dict[str, Optional[Any]]]]],
) -> None:
    """Save the results we uploaded to the user for later retrieval"""
    # Save the results we uploaded to the user for later retrieval
    # Saving access request URL's on the privacy request in case DSR 3.0
    # exits processing before the email is sent
    privacy_request.access_result_urls = {"access_result_urls": download_urls}
    privacy_request.save(session)

    # Try to save the backup results, but don't fail the DSR if this fails
    try:
        privacy_request.save_filtered_access_results(session, rule_filtered_results)
        logger.info("Successfully saved backup filtered access results to database")
    except (
        InternalError_,  # invalid memory alloc request size 1073741824
        sqlalchemy.exc.StatementError,  # SQL statement errors
        # Python memory errors
        MemoryError,  # system out of memory
        OverflowError,  # numeric overflow during serialization
    ) as exc:
        logger.warning(
            "Failed to save backup of DSR results to database after successful S3 upload. "
            "DSR will continue processing. Error: {}",
            str(exc),
        )
    except Exception as exc:
        logger.error(
            "Failed to save backup of DSR results to database after successful S3 upload. "
            "DSR will continue processing. Unexpected Error: {}",
            str(exc),
        )


@log_context(
    capture_args={
        "privacy_request_id": LoggerContextKeys.privacy_request_id,
    }
)
def upload_and_save_access_results(  # pylint: disable=R0912
    session: Session,
    policy: Policy,
    access_result: dict[str, list[Row]],
    dataset_graph: DatasetGraph,
    privacy_request: PrivacyRequest,
    manual_data_access_results: ManualWebhookResults,
    fides_connector_datasets: set[str],
) -> list[str]:
    """Process the data uploads after the access portion of the privacy request has completed"""
    download_urls: list[str] = []
    # Remove manual webhook attachments and request task attachments from the list of attachments
    # This is done because:
    # - manual webhook attachments are already included in the manual_data
    # - manual task submission attachments are already included in the manual_data
    # - request task attachments (from async polling) are already embedded in the dataset results
    loaded_attachments = [
        attachment
        for attachment in privacy_request.attachments
        if not any(
            ref.reference_type
            in [
                AttachmentReferenceType.access_manual_webhook,
                AttachmentReferenceType.manual_task_submission,
                AttachmentReferenceType.request_task,
            ]
            for ref in attachment.references
        )
    ]
    attachments = get_attachments_content(loaded_attachments)
    # Process attachments once for both upload and storage
    upload_attachments, storage_attachments = process_attachments_for_upload(
        attachments
    )

    if not access_result:
        logger.info("No results returned for access request")

    rule_filtered_results: dict[str, dict[str, list[dict[str, Optional[Any]]]]] = {}
    for rule in policy.get_rules_for_action(  # pylint: disable=R1702
        action_type=ActionType.access
    ):
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
        # Create a copy of filtered results to modify for upload
        results_to_upload = deepcopy(filtered_results)
        results_to_upload.update(manual_data_access_results.manual_data_for_upload)

        rule_download_urls = upload_access_results(
            session,
            policy,
            rule,
            results_to_upload,
            dataset_graph,
            privacy_request,
            upload_attachments,
        )
        download_urls.extend(rule_download_urls)

        # Create results for storage
        filtered_results.update(manual_data_access_results.manual_data_for_storage)
        if storage_attachments:
            filtered_results["attachments"] = storage_attachments
        rule_filtered_results[rule.key] = filtered_results

    save_access_results(session, privacy_request, download_urls, rule_filtered_results)
    return download_urls
