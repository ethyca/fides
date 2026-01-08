"""Configuration for OpenTelemetry tracing."""
from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from fides.config.fides_settings import FidesSettings

ENV_PREFIX = "FIDES__TRACING__"


class TracingSettings(FidesSettings):
    """Configuration for OpenTelemetry distributed tracing."""

    enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing for the application.",
    )

    service_name: str = Field(
        default="fides",
        description="Service name to use for tracing spans.",
    )

    otlp_endpoint: Optional[str] = Field(
        default=None,
        description="OTLP endpoint for exporting traces (e.g., http://localhost:4317 for gRPC or http://localhost:4318/v1/traces for HTTP).",
    )

    otlp_protocol: Optional[str] = Field(
        default="http/protobuf",
        description="OTLP protocol to use for exporting traces (http/protobuf or grpc).",
    )

    otlp_exporter: Optional[str] = Field(
        default="otlp",
        description="OTLP exporter to use for exporting traces (otlp or console).",
    )

    sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Sampling rate for traces (0.0 to 1.0). 1.0 means trace every request.",
    )

    console_exporter: bool = Field(
        default=False,
        description="Enable console exporter for debugging (logs traces to stdout).",
    )

    trace_db_queries: bool = Field(
        default=True,
        description="Enable detailed tracing of database queries via SQLAlchemy instrumentation.",
    )

    trace_http_client: bool = Field(
        default=True,
        description="Enable tracing of outbound HTTP requests via httpx instrumentation.",
    )

    trace_redis: bool = Field(
        default=True,
        description="Enable tracing of Redis operations.",
    )

    export_timeout_ms: int = Field(
        default=30000,
        description="Timeout in milliseconds for exporting traces.",
    )

    max_queue_size: int = Field(
        default=2048,
        description="Maximum queue size for the batch span processor.",
    )

    max_export_batch_size: int = Field(
        default=512,
        description="Maximum batch size for exporting spans.",
    )

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
