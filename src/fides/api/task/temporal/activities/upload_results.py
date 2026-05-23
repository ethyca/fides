"""Activity for uploading access results to storage."""

from __future__ import annotations

from temporalio import activity


@activity.defn
async def upload_access_results(privacy_request_id: str) -> list[str]:
    """Upload filtered access results to the configured storage destination.

    Reuses the existing upload_and_save_access_results logic from
    request_runner_service.py. Returns a list of download URLs.
    """
    from sqlalchemy.orm import selectinload

    from fides.api.graph.graph import DatasetGraph
    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.models.datasetconfig import DatasetConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.schemas.policy import ActionType
    from fides.api.service.privacy_request.request_runner_service import (
        apply_dataset_graph_filters,
        filter_by_enabled_actions,
        filter_fides_connector_datasets,
        get_manual_webhook_access_inputs,
        upload_and_save_access_results,
    )
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        policy = privacy_request.policy

        datasets = (
            session.query(DatasetConfig)
            .options(
                selectinload(DatasetConfig.connection_config),
                selectinload(DatasetConfig.ctl_dataset),
            )
            .all()
        )

        connection_configs = (
            session.query(ConnectionConfig)
            .options(selectinload(ConnectionConfig.datasets))
            .all()
        )

        dataset_graphs = [
            dc.get_graph() for dc in datasets if not dc.connection_config.disabled
        ]
        dataset_graphs = apply_dataset_graph_filters(
            dataset_graphs, privacy_request.property_id
        )
        dataset_graph = DatasetGraph(*dataset_graphs)

        raw_access_results = privacy_request.get_raw_access_results()
        filtered_access_results = filter_by_enabled_actions(
            raw_access_results, connection_configs
        )

        manual_webhook_access_results = get_manual_webhook_access_inputs(
            session, privacy_request, policy
        )

        fides_connector_datasets = filter_fides_connector_datasets(connection_configs)

        from fides.api.service.privacy_request.request_runner_service import (
            _load_and_process_attachments,
        )

        upload_attachments, storage_attachments = _load_and_process_attachments(
            privacy_request
        )

        access_result_urls = upload_and_save_access_results(
            session=session,
            policy=policy,
            access_result=filtered_access_results,
            dataset_graph=dataset_graph,
            privacy_request=privacy_request,
            manual_data_access_results=manual_webhook_access_results,
            fides_connector_datasets=fides_connector_datasets,
            upload_attachments=upload_attachments,
            storage_attachments=storage_attachments,
        )

        return access_result_urls or []
