"""
Integration example showing how metrics are exposed via the /api/v1/health/metrics endpoint.

This example demonstrates:
1. Automatic HTTP metrics via FastAPI Instrumentator
2. Creating custom metrics using the registry
3. Using decorators to instrument functions
4. How all metrics automatically appear at /api/v1/health/metrics
"""

from fides.api.metrics import count_and_time, count_calls, get_default_metrics_registry


# Example 1: Direct metric creation (uses Instrumentator's registry)
def create_some_metrics():
    """Create some metrics directly via the registry."""
    registry = get_default_metrics_registry()

    # Create a counter with namespace and subsystem
    api_requests = registry.counter(
        "requests_total",
        "Total API requests",
        namespace="fides",
        subsystem="api",
        labelnames=["method", "endpoint", "status"],
    )

    # Simulate some requests
    api_requests.labels(method="GET", endpoint="/api/users", status="200").inc(5)
    api_requests.labels(method="POST", endpoint="/api/users", status="201").inc(2)
    api_requests.labels(method="GET", endpoint="/api/health", status="200").inc(10)

    # Create a gauge
    active_connections = registry.gauge(
        "active_connections", "Number of active connections", namespace="fides"
    )
    active_connections.set(42)

    # Create a histogram for response times
    response_time = registry.histogram(
        "response_duration_seconds",
        "HTTP response duration in seconds",
        namespace="fides",
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    )

    # Simulate some response times
    response_time.observe(0.023)
    response_time.observe(0.156)
    response_time.observe(0.089)


# Example 2: Using decorators - these metrics are automatically registered
@count_calls("privacy_request_processing", namespace="fides")
def process_privacy_request(request_id: int) -> str:
    """Process a privacy request."""
    return f"Processed request {request_id}"


@count_and_time("database_query", namespace="fides", subsystem="db")
def execute_database_query(query: str) -> dict:
    """Execute a database query."""
    import time

    time.sleep(0.01)  # Simulate query execution
    return {"rows": 100, "query": query}


@count_calls("cache_hit", namespace="fides", labels={"cache_type": "redis"})
def check_cache(key: str) -> bool:
    """Check if key exists in cache."""
    return True


def demonstrate_metrics():
    """Demonstrate various metrics that will appear at /api/v1/health/metrics"""

    print("Creating metrics...")

    # Create some basic metrics
    create_some_metrics()

    # Use decorated functions to generate metrics
    for i in range(5):
        process_privacy_request(i)

    for query in ["SELECT * FROM users", "SELECT * FROM policies"]:
        execute_database_query(query)

    for key in ["user:123", "user:456", "user:789"]:
        check_cache(key)

    print("\nMetrics created! These will now appear at GET /api/v1/health/metrics")
    print("\nAutomatic HTTP metrics from Instrumentator:")
    print("  - http_request_duration_seconds{handler,method,status}")
    print("  - http_requests_total{handler,method,status}")
    print("  - http_requests_inprogress{handler,method}")
    print("\nCustom application metrics:")
    print("  - fides_api_requests_total{method,endpoint,status}")
    print("  - fides_active_connections")
    print("  - fides_response_duration_seconds_bucket{le}")
    print("  - fides_privacy_request_processing_calls_total")
    print("  - fides_db_database_query_calls_total")
    print("  - fides_db_database_query_duration_seconds_bucket{le}")
    print('  - fides_cache_hit_calls_total{cache_type="redis"}')
    print("\nYou can scrape these metrics with Prometheus or view them directly:")
    print("  curl http://localhost:8080/api/v1/health/metrics")
    print("\nControl metrics collection with environment variable:")
    print("  export ENABLE_METRICS=true  # Enable (default)")
    print("  export ENABLE_METRICS=false # Disable")


if __name__ == "__main__":
    demonstrate_metrics()
