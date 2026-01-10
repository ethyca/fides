"""
OpenTelemetry tracing utilities for Fides.

This module provides instrumentation for FastAPI and SQLAlchemy to enable
distributed tracing with minimal code changes.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from fastapi import FastAPI
from loguru import logger
from sqlalchemy.engine import Engine

from fides.config import FidesConfig

# OpenTelemetry imports are optional - app should work without them
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SpanExporter,
    )
    from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning(
        "OpenTelemetry packages not available. Tracing will be disabled. "
        "Install opentelemetry packages to enable tracing."
    )


def _create_otlp_exporter(config: FidesConfig) -> Optional[SpanExporter]:
    """Create OTLP exporter based on configuration."""
    if not config.tracing.otlp_endpoint:
        logger.warning("No OTLP endpoint configured")
        return None

    try:
        # Determine if we're using gRPC or HTTP based on the endpoint
        endpoint = config.tracing.otlp_endpoint
        protocol = config.tracing.otlp_protocol
        exporter = config.tracing.otlp_exporter

        if protocol == "http/protobuf":
            logger.info(f"Configuring OTLP HTTP trace exporter to {endpoint}")
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter as HTTPOTLPSpanExporter,
            )
            return HTTPOTLPSpanExporter(
                endpoint=endpoint,
                timeout=config.tracing.export_timeout_ms // 1000,
            )
        elif protocol == "grpc":
            logger.info(f"Configuring OTLP gRPC trace exporter to {endpoint}")
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter as GRPCOTLPSpanExporter,
            )
            return GRPCOTLPSpanExporter(
                endpoint=endpoint,
                timeout=config.tracing.export_timeout_ms // 1000,
            )
        else:
            logger.warning(f"Unsupported OTLP protocol: {protocol}")
            return None

    except Exception as e:
        logger.warning(f"Failed to create OTLP exporter: {e}")
        return None


def setup_tracing(config: FidesConfig) -> Optional[TracerProvider]:
    """
    Set up OpenTelemetry tracing based on configuration.

    Args:
        config: Fides configuration object

    Returns:
        TracerProvider if tracing is enabled, None otherwise
    """
    if not config.tracing.enabled:
        logger.info("Tracing is disabled in configuration")
        return None

    if not OPENTELEMETRY_AVAILABLE:
        logger.warning(
            "Tracing is enabled but OpenTelemetry packages are not available. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy"
        )
        return None

    try:
        logger.info(f"Setting up tracing for service '{config.tracing.service_name}'")
        # Create resource with service name
        resource = Resource(attributes={SERVICE_NAME: config.tracing.service_name})

        # Create sampler based on sample rate
        sampler = ParentBasedTraceIdRatio(config.tracing.sample_rate)



        # Create tracer provider
        provider = TracerProvider(resource=resource, sampler=sampler)

        # Add exporters
        exporters_added = False

        # Console exporter for debugging
        if config.tracing.console_exporter:
            logger.info("Adding console span exporter")
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("Added console span exporter")
            exporters_added = True

        # OTLP exporter for production
        otlp_exporter = _create_otlp_exporter(config)
        if otlp_exporter:
            logger.info(f"Adding OTLP span exporter to {config.tracing.otlp_endpoint}")
            provider.add_span_processor(
                BatchSpanProcessor(
                    otlp_exporter,
                    max_queue_size=config.tracing.max_queue_size,
                    max_export_batch_size=config.tracing.max_export_batch_size,
                )
            )
            logger.info(f"Added OTLP span exporter to {config.tracing.otlp_endpoint}")
            exporters_added = True

        if not exporters_added:
            logger.warning(
                "Tracing is enabled but no exporters are configured. "
                "Set FIDES__TRACING__OTLP_ENDPOINT or FIDES__TRACING__CONSOLE_EXPORTER=true"
            )
            return None

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        logger.info(
            f"OpenTelemetry tracing initialized for service '{config.tracing.service_name}' "
            f"with sample rate {config.tracing.sample_rate}"
        )

        return provider

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")
        return None


def instrument_fastapi(app: FastAPI, config: FidesConfig) -> None:
    """
    Instrument FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance
        config: Fides configuration object
    """
    if not config.tracing.enabled or not OPENTELEMETRY_AVAILABLE:
        logger.info("FastAPI tracing is disabled in configuration or OpenTelemetry is not available")
        return

    try:
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=trace.get_tracer_provider(),
            excluded_urls="/static/*,/_next/*",
        )
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def instrument_sqlalchemy(engine: Engine, config: FidesConfig, extra_tags: Optional[dict[str, Any]] = None) -> None:
    """
    Instrument SQLAlchemy engine with OpenTelemetry.

    Args:
        engine: SQLAlchemy engine instance
        config: Fides configuration object
    """
    if not config.tracing.enabled or not config.tracing.trace_db_queries:
        return

    if not OPENTELEMETRY_AVAILABLE:
        return

    try:


        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            tracer_provider=trace.get_tracer_provider(),
            enable_attribute_commenter=True,
            commenter_options=extra_tags if extra_tags is not None else {},
            enable_commenter=True
        )
        logger.info(f"SQLAlchemy instrumentation enabled for engine: {engine.url.database}")
    except Exception as e:
        logger.error(f"Failed to instrument SQLAlchemy: {e}")


def instrument_httpx(config: FidesConfig) -> None:
    """
    Instrument httpx client with OpenTelemetry for tracing outbound HTTP requests.

    Args:
        config: Fides configuration object
    """
    if not config.tracing.enabled or not config.tracing.trace_http_client:
        return

    if not OPENTELEMETRY_AVAILABLE:
        return

    try:
        HTTPXClientInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider(),
        )
        logger.info("httpx client instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument httpx: {e}")


def instrument_redis(config: FidesConfig) -> None:
    """
    Instrument Redis client with OpenTelemetry.

    Args:
        config: Fides configuration object
    """
    if not config.tracing.enabled or not config.tracing.trace_redis:
        return

    if not OPENTELEMETRY_AVAILABLE:
        return

    try:
        RedisInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider(),
        )
        logger.info("Redis instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument Redis: {e}")


@contextmanager
def trace_span(
    name: str, attributes: Optional[Dict[str, Any]] = None
) -> Generator[Any, None, None]:
    """
    Context manager for creating custom trace spans.

    Example:
        with trace_span("process_privacy_request", {"request_id": "123"}):
            # Your code here
            pass

    Args:
        name: Name of the span
        attributes: Optional dictionary of attributes to attach to the span

    Yields:
        The span object (or None if tracing is disabled)
    """
    if not OPENTELEMETRY_AVAILABLE:
        yield None
        return

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                # Convert value to string if it's not a primitive type
                if not isinstance(value, (str, int, float, bool)):
                    value = str(value)
                span.set_attribute(key, value)
        yield span


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """
    Add attributes to the current active span.

    Example:
        add_span_attributes({"user_id": "123", "operation": "delete"})

    Args:
        attributes: Dictionary of attributes to add to the current span
    """
    if not OPENTELEMETRY_AVAILABLE:
        return

    try:
        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in attributes.items():
                # Convert value to string if it's not a primitive type
                if not isinstance(value, (str, int, float, bool)):
                    value = str(value)
                span.set_attribute(key, value)
    except Exception as e:
        logger.debug(f"Failed to add span attributes: {e}")


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add an event to the current active span.

    Example:
        add_span_event("cache_hit", {"key": "user:123"})

    Args:
        name: Name of the event
        attributes: Optional dictionary of attributes for the event
    """
    if not OPENTELEMETRY_AVAILABLE:
        return

    try:
        span = trace.get_current_span()
        if span and span.is_recording():
            if attributes:
                # Convert non-primitive types to strings
                attrs = {
                    k: v if isinstance(v, (str, int, float, bool)) else str(v)
                    for k, v in attributes.items()
                }
                span.add_event(name, attributes=attrs)
            else:
                span.add_event(name)
    except Exception as e:
        logger.debug(f"Failed to add span event: {e}")


def get_tracer(name: str) -> Any:
    """
    Get a tracer for creating custom spans.

    Example:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("custom_operation"):
            # Your code here
            pass

    Args:
        name: Name of the tracer (typically __name__ of the module)

    Returns:
        Tracer object or a no-op tracer if OpenTelemetry is not available
    """
    if not OPENTELEMETRY_AVAILABLE:
        # Return a dummy object that does nothing
        class NoOpTracer:
            @contextmanager
            def start_as_current_span(self, name: str, **kwargs: Any) -> Generator[None, None, None]:
                yield None

        return NoOpTracer()

    return trace.get_tracer(name)
