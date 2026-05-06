"""OpenTelemetry-style tracing for Celery tasks (log-based exporter).

When ``logging.celery_otel_tracing`` is true (the default), trace context is injected into
Celery message headers and restored in workers. Completed spans are logged at
INFO via Loguru (no OTLP backend required). Set the flag to false to disable.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from celery import Task
from celery.signals import before_task_publish, task_failure, task_postrun, task_prerun
from loguru import logger
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.propagators.textmap import Getter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from fides.config import FidesConfig

_F = TypeVar("_F", bound=Callable[..., Any])

_TRACER_PROVIDER_INSTALLED = False
_CELERY_TRACING_ENABLED = False

# Stack of (task root span, (detach_token_for_parent_ctx, detach_token_for_span_ctx)).
# Nested tasks (e.g. ``apply()`` from inside another task) must not clobber the parent
# handle: ``task_postrun`` runs inner-to-outer, matching push/pop order.
_task_otel_stack: ContextVar[Optional[List[Tuple[Span, Tuple[Any, Any]]]]] = ContextVar(
    "fides_celery_task_otel_stack", default=None
)

_PROPAGATOR = TraceContextTextMapPropagator()


class _CeleryHeadersGetter(Getter[Dict[str, Any]]):
    """Getter for Kombu/Celery headers (values may be str, bytes, or single-element lists)."""

    def get(self, carrier: Dict[str, Any], key: str) -> Optional[List[str]]:
        if key not in carrier:
            return None
        value = carrier[key]
        if isinstance(value, (list, tuple)):
            value = value[0] if value else None
        if value is None:
            return None
        if isinstance(value, bytes):
            return [value.decode("utf-8", errors="replace")]
        return [str(value)]

    def keys(self, carrier: Dict[str, Any]) -> List[str]:
        return list(carrier.keys())


_HEADER_GETTER = _CeleryHeadersGetter()


def _celery_carrier_set(carrier: Dict[str, Any], key: str, value: str) -> None:
    carrier[key] = value


class _LogSpanExporter(SpanExporter):
    """Exports completed spans by emitting a structured Loguru INFO line."""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            ctx = span.get_span_context()
            attrs = dict(span.attributes or {}) if span.attributes else {}
            trace_id = format(ctx.trace_id, "032x") if ctx.trace_id else None
            span_id = format(ctx.span_id, "016x") if ctx.span_id else None
            parent_span_id: Optional[str] = None
            parent = getattr(span, "parent", None)
            if parent is not None and getattr(parent, "span_id", None):
                parent_span_id = format(parent.span_id, "016x")

            start_ns = span.start_time
            end_ns = span.end_time
            duration_ms: Optional[float] = None
            if (
                isinstance(start_ns, int)
                and isinstance(end_ns, int)
                and end_ns >= start_ns
            ):
                # OpenTelemetry uses nanoseconds since Unix epoch for SDK timestamps.
                duration_ms = (end_ns - start_ns) / 1_000_000

            logger.bind(
                trace_id=trace_id,
                span_id=span_id,
                span_name=span.name,
                parent_span_id=parent_span_id,
                span_start_unix_ns=start_ns,
                span_end_unix_ns=end_ns,
                span_duration_ms=duration_ms,
                attributes=json.dumps(attrs, default=str, sort_keys=True),
            ).info("otel.celery.span")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def configure_celery_tracing(config: FidesConfig) -> None:
    """
    Install a global TracerProvider when enabled.

    Celery signal receivers are registered once at import time; they no-op until
    this sets ``_CELERY_TRACING_ENABLED`` to True.

    No-ops when ``config.logging.celery_otel_tracing`` is false. If the attribute
    is missing, tracing defaults to on (``getattr(..., True)``).
    """
    global _TRACER_PROVIDER_INSTALLED  # noqa: PLW0603
    global _CELERY_TRACING_ENABLED  # noqa: PLW0603

    if not getattr(config.logging, "celery_otel_tracing", True):
        _CELERY_TRACING_ENABLED = False
        return

    _CELERY_TRACING_ENABLED = True

    if _TRACER_PROVIDER_INSTALLED:
        return

    resource = Resource.create({SERVICE_NAME: "fides-celery"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(_LogSpanExporter()))
    trace.set_tracer_provider(provider)
    _TRACER_PROVIDER_INSTALLED = True


@before_task_publish.connect(dispatch_uid="fides_otel_before_task_publish", weak=False)
def _inject_trace_headers(
    signal: Any = None,  # noqa: ARG001
    sender: Any = None,  # noqa: ARG001
    body: Any = None,  # noqa: ARG001
    exchange: Any = None,  # noqa: ARG001
    routing_key: str = "",
    headers: Optional[Dict[str, Any]] = None,
    properties: Any = None,  # noqa: ARG001
    declare: Any = None,  # noqa: ARG001
    retry_policy: Any = None,  # noqa: ARG001
    **kwargs: Any,  # Celery requires VAR_KEYWORD for signal receivers
) -> None:
    if not _CELERY_TRACING_ENABLED:
        return
    if headers is None:
        return
    ctx = otel_context.get_current()
    _PROPAGATOR.inject(headers, context=ctx, setter=_celery_carrier_set)


@task_prerun.connect(dispatch_uid="fides_otel_task_prerun", weak=False)
def _start_task_span(task: Task, **_kwargs: Any) -> None:
    if not _CELERY_TRACING_ENABLED:
        return

    carrier: Dict[str, Any] = {}
    raw_headers = getattr(task.request, "headers", None) or {}
    if isinstance(raw_headers, dict):
        carrier = cast(Dict[str, Any], raw_headers)

    parent_ctx: Context = _PROPAGATOR.extract(
        carrier,
        context=otel_context.get_current(),
        getter=_HEADER_GETTER,
    )
    detach_task = otel_context.attach(parent_ctx)

    tracer = trace.get_tracer(__name__)
    task_name = getattr(task, "name", None) or getattr(
        getattr(task, "request", None), "task", "celery.unknown_task"
    )
    span = tracer.start_span(
        str(task_name),
        attributes={
            "celery.task_id": getattr(getattr(task, "request", None), "id", ""),
            "celery.task_name": str(task_name),
            "celery.args_count": len(getattr(task.request, "args", ()) or ()),
            "celery.kwargs_count": len(getattr(task.request, "kwargs", {}) or {}),
        },
    )
    span_ctx = trace.set_span_in_context(span)
    detach_span = otel_context.attach(span_ctx)
    stack = list(_task_otel_stack.get() or [])
    stack.append((span, (detach_task, detach_span)))
    _task_otel_stack.set(stack)


@task_failure.connect(dispatch_uid="fides_otel_task_failure", weak=False)
def _record_task_failure(task: Task, exception: BaseException, **_kwargs: Any) -> None:  # noqa: ARG001
    if not _CELERY_TRACING_ENABLED:
        return
    stack = _task_otel_stack.get() or []
    if not stack:
        return
    span, _tokens = stack[-1]
    span.record_exception(exception)
    span.set_status(Status(StatusCode.ERROR, str(exception)))


@task_postrun.connect(dispatch_uid="fides_otel_task_postrun", weak=False)
def _finish_task_span(task: Task, **_kwargs: Any) -> None:  # noqa: ARG001
    if not _CELERY_TRACING_ENABLED:
        return
    stack = list(_task_otel_stack.get() or [])
    if not stack:
        return
    span, (detach_task, detach_span) = stack.pop()
    _task_otel_stack.set(stack if stack else None)
    try:
        if span.status.status_code == StatusCode.UNSET:
            span.set_status(Status(StatusCode.OK))
    finally:
        span.end()
        otel_context.detach(detach_span)
        otel_context.detach(detach_task)


@contextmanager
def celery_step_span(name: str, **attrs: Any) -> Generator[Optional[Span], None, None]:
    """Create a **child** span for work inside a Celery task (same trace, new span).

    Celery's per-task root span is started in ``task_prerun`` and attached to the
    current OpenTelemetry context. ``celery_step_span`` starts a nested span as a
    child of whatever span is current—typically the task span—so exported logs
    share the same ``trace_id`` and show parent/child timing via ``span_duration_ms``.

    **Context manager (inline blocks)**

    .. code-block:: python

        @celery_app.task
        def run_dsr(task_id: str) -> None:
            with celery_step_span("dsr.load_graph"):
                ...
            with celery_step_span("dsr.execute", phase="access"):
                ...

    **Decorator (inner helpers)**

    Prefer :func:`celery_traced_function` for plain functions/methods you call from
    tasks—same behavior, less nesting.

    When tracing is disabled, yields ``None`` and performs no work.
    """
    if not _CELERY_TRACING_ENABLED:
        yield None
        return

    tracer = trace.get_tracer(__name__)
    span = tracer.start_span(name, attributes=attrs or None)
    token = otel_context.attach(trace.set_span_in_context(span))
    try:
        yield span
    finally:
        span.end()
        otel_context.detach(token)


def celery_traced_function(
    func: Optional[_F] = None,
    *,
    name: Optional[str] = None,
    **attrs: Any,
) -> Union[_F, Callable[[_F], _F]]:
    """Wrap a callable in :func:`celery_step_span` (child span, same trace).

    Supports both bare and parametrized decorator styles:

    .. code-block:: python

        @celery_traced_function
        def heavy_step(x: int) -> int:
            return x * 2

        @celery_traced_function(name="privacy_request.normalize_payload", kind="normalize")
        def normalize(payload: dict) -> dict:
            return payload

    The default span name is ``{module}.{qualname}`` of the wrapped function.
    """

    def decorator(fn: _F) -> _F:
        span_name = name or f"{fn.__module__}.{fn.__qualname__}"

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with celery_step_span(span_name, **attrs):
                return fn(*args, **kwargs)

        return cast(_F, wrapper)

    if func is not None:
        return decorator(func)
    return decorator
