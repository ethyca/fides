"""Tests for Celery OpenTelemetry-style tracing (log export + trace context).

These tests validate:

- Span export logs (``otel.celery.span``) are emitted for executed tasks.
- DSR ``GraphTask`` SQL / SaaS connector steps emit **child** spans that share the
  Celery task ``trace_id`` (see ``dsr.graph_task.*`` span names).
- A task can join an existing trace when W3C ``traceparent`` is present on the
  Celery message headers (the mechanism used for cross-task propagation).

Tasks are invoked with ``Task.apply()`` so Celery's eager trace pipeline runs
(``task_prerun`` / ``task_postrun``). ``Task.run()`` skips that pipeline, so OTEL
hooks would not emit spans. ``delay().get()`` is avoided because it blocks on the
result backend when workers are not consuming the queue.

Note: asserting *automatic* propagation for nested ``.delay()`` calls inside
another task is brittle under ``task_always_eager`` (Celery publish/signal
behavior varies). The nested test below mirrors what ``before_task_publish``
injection is meant to accomplish by explicitly injecting trace context before
scheduling the child task.

``logging.celery_otel_tracing`` defaults to false in application config; an
autouse fixture in this module enables it and re-runs ``configure_celery_tracing``
so these tests still validate span export.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest import mock
from uuid import uuid4

import pytest
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from fides.config import CONFIG
from fides.observability.celery_tracing import configure_celery_tracing

_PROPAGATOR = TraceContextTextMapPropagator()


@pytest.fixture(autouse=True)
def _enable_celery_otel_tracing_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Application default is off; turn tracing on for span assertions in this file."""
    monkeypatch.setattr(
        CONFIG,
        "logging",
        CONFIG.logging.model_copy(update={"celery_otel_tracing": True}),
    )
    configure_celery_tracing(CONFIG)


def _record_message(record: Any) -> str:
    return getattr(record, "message", None) or record.getMessage()


def _span_export_records(loguru_caplog: Any) -> List[Any]:
    return [
        r for r in loguru_caplog.records if _record_message(r) == "otel.celery.span"
    ]


def _record_extra(record: Any) -> Dict[str, Any]:
    return dict(getattr(record, "extra", {}) or {})


def _extra_attrs(record: Any) -> Dict[str, Any]:
    extra = _record_extra(record)
    raw = extra.get("attributes")
    if isinstance(raw, str):
        return json.loads(raw)
    return {}


def test_celery_otel_emits_span_log_for_task(
    celery_session_app: Any,
    celery_session_worker: Any,
    loguru_caplog: Any,
) -> None:
    suffix = uuid4().hex[:10]
    task_name = f"otel_span_log_test_{suffix}"

    @celery_session_app.task(name=task_name)
    def _otel_sample_task() -> str:
        return "done"

    celery_session_worker.reload()

    loguru_caplog.clear()
    # Use ``apply()`` (not ``run()``): ``run()`` bypasses Celery's trace pipeline, so
    # ``task_prerun`` / ``task_postrun`` never fire and OTEL span export won't run.
    result = _otel_sample_task.apply()
    assert result.successful()
    assert result.result == "done"

    recs = _span_export_records(loguru_caplog)
    assert recs, "expected at least one otel.celery.span INFO log from span export"

    match = next(
        (
            r
            for r in recs
            if _record_extra(r).get("span_name") == task_name
            or _extra_attrs(r).get("celery.task_name") == task_name
        ),
        None,
    )
    assert match is not None, (
        "expected a span for the test task; "
        f"span_names={[(_record_extra(r).get('span_name'), _extra_attrs(r).get('celery.task_name')) for r in recs]}"
    )

    extra = _record_extra(match)
    assert extra.get("trace_id")
    assert extra.get("span_id")


def test_celery_otel_task_joins_trace_from_traceparent_headers(
    celery_session_app: Any,
    celery_session_worker: Any,
    loguru_caplog: Any,
) -> None:
    suffix = uuid4().hex[:10]
    task_name = f"otel_header_join_{suffix}"

    @celery_session_app.task(name=task_name)
    def _otel_join_task() -> str:
        return "joined"

    celery_session_worker.reload()

    carrier: Dict[str, Any] = {}
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("celery_otel_publish_root"):
        expected_trace_id = format(
            trace.get_current_span().get_span_context().trace_id, "032x"
        )
        _PROPAGATOR.inject(carrier, context=otel_context.get_current())

    assert "traceparent" in carrier, (
        "expected W3C trace context injection to populate traceparent"
    )

    loguru_caplog.clear()
    eager_result = _otel_join_task.apply(headers=dict(carrier))
    assert eager_result.successful()
    assert eager_result.result == "joined"

    recs = _span_export_records(loguru_caplog)
    match = next(
        (
            r
            for r in recs
            if _record_extra(r).get("span_name") == task_name
            or _extra_attrs(r).get("celery.task_name") == task_name
        ),
        None,
    )
    assert match is not None, (
        "expected a span for the test task; "
        f"span_names={[(_record_extra(r).get('span_name'), _extra_attrs(r).get('celery.task_name')) for r in recs]}"
    )

    assert _record_extra(match).get("trace_id") == expected_trace_id


def test_celery_otel_nested_tasks_share_trace_when_traceparent_is_injected(
    celery_session_app: Any,
    celery_session_worker: Any,
    loguru_caplog: Any,
) -> None:
    """Parent schedules child with explicit traceparent headers (mirrors publish-time inject)."""
    suffix = uuid4().hex[:10]
    child_name = f"otel_nested_child_{suffix}"
    parent_name = f"otel_nested_parent_{suffix}"

    @celery_session_app.task(name=child_name)
    def _child() -> str:
        return "child"

    @celery_session_app.task(name=parent_name)
    def _parent() -> str:
        carrier: Dict[str, Any] = {}
        _PROPAGATOR.inject(carrier, context=otel_context.get_current())
        child_result = _child.apply(headers=dict(carrier))
        assert child_result.successful()
        assert child_result.result == "child"
        return "parent"

    celery_session_worker.reload()

    loguru_caplog.clear()
    parent_result = _parent.apply()
    assert parent_result.successful()
    assert parent_result.result == "parent"

    recs = _span_export_records(loguru_caplog)
    ours = [
        r
        for r in recs
        if _record_extra(r).get("span_name") in (parent_name, child_name)
        or _extra_attrs(r).get("celery.task_name") in (parent_name, child_name)
    ]

    assert len(ours) == 2, (
        "expected parent and child task spans; "
        f"matched={len(ours)} otel span logs; span_names="
        f"{[_record_extra(r).get('span_name') for r in recs]}"
    )

    trace_ids = {_record_extra(r).get("trace_id") for r in ours}
    trace_ids.discard(None)
    assert len(trace_ids) == 1, (
        f"expected one trace_id across nested tasks, got {trace_ids}"
    )


def _build_postgres_graph_task_for_otel(
    db: Any, privacy_request: Any, policy: Any
) -> Any:
    """Minimal persisted RequestTask + postgres ``GraphTask`` (matches traversal-only tests)."""
    from fides.api.graph.config import (
        Collection,
        GraphDataset,
        PropertyScope,
        ScalarField,
    )
    from fides.api.graph.graph import Node
    from fides.api.graph.traversal import TraversalNode
    from fides.api.models.connectionconfig import (
        AccessLevel,
        ConnectionConfig,
        ConnectionType,
    )
    from fides.api.models.worker_task import ExecutionLogStatus
    from fides.api.schemas.policy import ActionType
    from fides.api.task.graph_task import GraphTask
    from fides.api.task.task_resources import TaskResources

    connection_key = f"otel_sql_graph_{uuid4().hex[:10]}"
    coll = Collection(
        name="otel_coll",
        fields=[ScalarField(name="id")],
        property_scope=PropertyScope.IN_SCOPE,
    )
    ds = GraphDataset(
        name="otel_ds",
        collections=[coll],
        connection_key=connection_key,
    )
    node = Node(ds, coll)
    tn = TraversalNode(node)
    rq = tn.to_mock_request_task()
    rq.action_type = ActionType.access
    rq.status = ExecutionLogStatus.pending
    rq.id = str(uuid4())
    db.add(rq)
    db.commit()

    resources = TaskResources(
        privacy_request,
        policy,
        [
            ConnectionConfig(
                key=connection_key,
                connection_type=ConnectionType.postgres,
                access=AccessLevel.write,
            )
        ],
        rq,
        db,
    )
    return GraphTask(resources)


def _build_saas_graph_task_for_otel(
    db: Any,
    privacy_request: Any,
    policy: Any,
    saas_example_connection_config: Any,
) -> Any:
    """``GraphTask`` wired to the standard SaaS example connection (see ``TestGraphTaskLogging``)."""
    from fides.api.graph.traversal import TraversalNode
    from fides.api.models.worker_task import ExecutionLogStatus
    from fides.api.schemas.policy import ActionType
    from fides.api.task.graph_task import EMPTY_REQUEST_TASK, GraphTask
    from fides.api.task.task_resources import TaskResources
    from tests.ops.graph.graph_test_util import generate_node

    resources = TaskResources(
        privacy_request,
        policy,
        [saas_example_connection_config],
        EMPTY_REQUEST_TASK,
        db,
    )
    tn = TraversalNode(generate_node("saas_ds", "saas_coll", "id"))
    tn.node.dataset.connection_key = saas_example_connection_config.key
    rq = tn.to_mock_request_task()
    rq.action_type = ActionType.access
    rq.status = ExecutionLogStatus.pending
    rq.id = str(uuid4())
    db.add(rq)
    db.commit()
    resources.privacy_request_task = rq
    return GraphTask(resources)


@mock.patch("fides.api.task.graph_task.GraphTask.access_results_post_processing")
@mock.patch("fides.api.service.connectors.sql_connector.SQLConnector.retrieve_data")
def test_celery_otel_dsr_sql_graph_task_access_emits_child_span_sharing_trace_id(
    mock_retrieve: Any,
    mock_post_processing: Any,
    celery_session_app: Any,
    celery_session_worker: Any,
    loguru_caplog: Any,
    db: Any,
    privacy_request: Any,
    policy: Any,
) -> None:
    """``dsr.graph_task.access`` is a child span of the Celery task (same ``trace_id``)."""
    mock_retrieve.return_value = [{"id": 1}]
    mock_post_processing.return_value = [{"id": 1}]

    graph_task = _build_postgres_graph_task_for_otel(db, privacy_request, policy)

    suffix = uuid4().hex[:10]
    task_name = f"otel_dsr_sql_access_{suffix}"

    @celery_session_app.task(name=task_name)
    def _run_sql_graph_access() -> str:
        graph_task.access_request()
        return "done"

    celery_session_worker.reload()
    loguru_caplog.clear()
    result = _run_sql_graph_access.apply()
    assert result.successful()
    assert result.result == "done"

    recs = _span_export_records(loguru_caplog)
    assert recs, "expected otel span export logs"

    parent = next(
        (
            r
            for r in recs
            if _record_extra(r).get("span_name") == task_name
            or _extra_attrs(r).get("celery.task_name") == task_name
        ),
        None,
    )
    assert parent is not None, (
        f"expected Celery task span; got span_names={[_record_extra(r).get('span_name') for r in recs]}"
    )

    child = next(
        (
            r
            for r in recs
            if _record_extra(r).get("span_name") == "dsr.graph_task.access"
        ),
        None,
    )
    assert child is not None, "expected dsr.graph_task.access child span"

    p_extra = _record_extra(parent)
    c_extra = _record_extra(child)
    assert c_extra.get("trace_id") == p_extra.get("trace_id")
    assert c_extra.get("parent_span_id") == p_extra.get("span_id")

    attrs = _extra_attrs(child)
    assert attrs.get("dsr.connector.family") == "sql"
    assert attrs.get("dsr.node.action") == "access"
    assert attrs.get("dsr.node.connection_type") == "postgres"
    assert c_extra.get("span_duration_ms") is not None


@mock.patch("fides.api.task.graph_task.GraphTask.access_results_post_processing")
@mock.patch("fides.api.service.connectors.saas_connector.SaaSConnector.retrieve_data")
def test_celery_otel_dsr_saas_graph_task_access_emits_child_span_sharing_trace_id(
    mock_retrieve: Any,
    mock_post_processing: Any,
    celery_session_app: Any,
    celery_session_worker: Any,
    loguru_caplog: Any,
    db: Any,
    privacy_request: Any,
    policy: Any,
    saas_example_connection_config: Any,
) -> None:
    """SaaS Tier-A node span shares ``trace_id`` with the enclosing Celery task span."""
    mock_retrieve.return_value = [{"id": 1}]
    mock_post_processing.return_value = [{"id": 1}]

    graph_task = _build_saas_graph_task_for_otel(
        db, privacy_request, policy, saas_example_connection_config
    )

    suffix = uuid4().hex[:10]
    task_name = f"otel_dsr_saas_access_{suffix}"

    @celery_session_app.task(name=task_name)
    def _run_saas_graph_access() -> str:
        graph_task.access_request()
        return "done"

    celery_session_worker.reload()
    loguru_caplog.clear()
    result = _run_saas_graph_access.apply()
    assert result.successful()
    assert result.result == "done"

    recs = _span_export_records(loguru_caplog)
    assert recs, "expected otel span export logs"

    parent = next(
        (
            r
            for r in recs
            if _record_extra(r).get("span_name") == task_name
            or _extra_attrs(r).get("celery.task_name") == task_name
        ),
        None,
    )
    assert parent is not None, (
        f"expected Celery task span; got span_names={[_record_extra(r).get('span_name') for r in recs]}"
    )

    child = next(
        (
            r
            for r in recs
            if _record_extra(r).get("span_name") == "dsr.graph_task.access"
        ),
        None,
    )
    assert child is not None, "expected dsr.graph_task.access child span"

    p_extra = _record_extra(parent)
    c_extra = _record_extra(child)
    assert c_extra.get("trace_id") == p_extra.get("trace_id")
    assert c_extra.get("parent_span_id") == p_extra.get("span_id")

    attrs = _extra_attrs(child)
    assert attrs.get("dsr.connector.family") == "saas"
    assert attrs.get("dsr.node.action") == "access"
    assert attrs.get("dsr.node.connection_type") == "saas"
    assert attrs.get("dsr.node.saas_version")
    assert c_extra.get("span_duration_ms") is not None
