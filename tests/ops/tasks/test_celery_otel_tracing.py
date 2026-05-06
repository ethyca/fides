"""Tests for Celery OpenTelemetry-style tracing (log export + trace context).

These tests validate:

- Span export logs (``otel.celery.span``) are emitted for executed tasks.
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
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from fides.config import CONFIG

_PROPAGATOR = TraceContextTextMapPropagator()


def _record_message(record: Any) -> str:
    return getattr(record, "message", None) or record.getMessage()


def _span_export_records(loguru_caplog: Any) -> List[Any]:
    return [
        r
        for r in loguru_caplog.records
        if _record_message(r) == "otel.celery.span"
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
    if not CONFIG.logging.celery_otel_tracing:
        pytest.skip("celery_otel_tracing disabled in config")

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
    if not CONFIG.logging.celery_otel_tracing:
        pytest.skip("celery_otel_tracing disabled in config")

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

    assert "traceparent" in carrier, "expected W3C trace context injection to populate traceparent"

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
    if not CONFIG.logging.celery_otel_tracing:
        pytest.skip("celery_otel_tracing disabled in config")

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
    assert len(trace_ids) == 1, f"expected one trace_id across nested tasks, got {trace_ids}"
