# Fides Metrics Module

A simple and convenient wrapper around Prometheus metrics for the Fides API, integrated with FastAPI Prometheus Instrumentator.

## Features

- **Simple Registry**: Create or retrieve metrics by name with automatic registration
- **Decorators**: Easily add counting and timing to functions and methods
- **Async Support**: Full support for async functions
- **Type Safe**: Fully typed with mypy
- **Flexible**: Supports namespaces, subsystems, and labels
- **Automatic Exposure**: Metrics are automatically exposed at `/api/v1/health/metrics`
- **FastAPI Instrumentation**: Automatic HTTP request metrics via Prometheus Instrumentator

## Installation

The required dependencies are included in `requirements.txt`:
- `prometheus-client==0.21.1`
- `prometheus-fastapi-instrumentator==7.0.0`

## Automatic HTTP Metrics

The FastAPI Instrumentator automatically provides these metrics for all HTTP endpoints:

- `http_request_duration_seconds` - HTTP request duration (histogram)
- `http_requests_total` - Total HTTP requests (counter)
- `http_requests_inprogress` - HTTP requests currently in progress (gauge)

Configuration (in `app_setup.py`):
```python
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="inprogress",
    inprogress_labels=True,
)
```

## Metrics Endpoint

All metrics (both automatic HTTP metrics and custom metrics) are exposed at:

```
GET /api/v1/health/metrics
```

This endpoint returns metrics in Prometheus text-based exposition format, which can be scraped by Prometheus servers.

Example response:
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{handler="/api/v1/users",method="GET",status="2xx"} 42.0

# HELP fides_api_requests_total Total number of API requests
# TYPE fides_api_requests_total counter
fides_api_requests_total{method="GET",endpoint="/api/users",status="200"} 42.0
```

## Usage

### Custom Metrics

All custom metrics created with `MetricsRegistry` are automatically registered with the Instrumentator's registry.

### Basic Registry Usage

```python
from fides.api.metrics import get_default_metrics_registry

# Get the default global registry
registry = get_default_metrics_registry()

# Create or get a counter
requests_counter = registry.counter('requests_total', 'Total requests')
requests_counter.inc()

# Create or get a gauge
active_connections = registry.gauge('active_connections', 'Active connections')
active_connections.set(42)

# Create or get a histogram
request_duration = registry.histogram(
    'request_duration_seconds',
    'Request duration',
    buckets=[0.1, 0.5, 1.0, 5.0]
)
request_duration.observe(0.25)

# Metrics with labels
http_requests = registry.counter(
    'http_requests_total',
    'HTTP requests',
    labelnames=['method', 'endpoint', 'status']
)
http_requests.labels(method='GET', endpoint='/api/users', status='200').inc()
```

### Using Decorators

#### Count Function Calls

```python
from fides.api.metrics import count_calls

@count_calls('api_calls', namespace='fides', subsystem='api')
def handle_request(request):
    return process(request)

# Async functions work too
@count_calls('async_operations')
async def async_handler():
    return await process_async()
```

#### Time Function Execution

```python
from fides.api.metrics import time_calls

@time_calls('request_duration_seconds', buckets=[0.1, 0.5, 1.0, 5.0])
def handle_request(request):
    return process(request)

# Use a Summary instead of Histogram
@time_calls('processing_time', use_histogram=False)
def process_data(data):
    return transform(data)
```

#### Count and Time Together

```python
from fides.api.metrics import count_and_time

@count_and_time('api_handler', namespace='fides')
def handle_api_request(endpoint: str):
    return {"status": "success", "endpoint": endpoint}

# Async support
@count_and_time('async_handler')
async def async_handler(request_id: int):
    return await process_async(request_id)
```

#### Using Labels with Decorators

```python
@count_calls('http_requests', labels={'method': 'GET', 'endpoint': '/api/users'})
def get_users():
    return fetch_users()

@time_calls('api_timing', labels={'service': 'user-service'})
def call_user_service():
    return make_request()
```

### Custom Registry

For testing or isolation purposes, you can create a custom registry. Note that metrics created with a custom registry will NOT be exposed at the `/api/v1/health/metrics` endpoint.

```python
from prometheus_client import CollectorRegistry, generate_latest
from fides.api.metrics import MetricsRegistry

# Create a custom registry for isolation (useful in tests)
custom_registry = CollectorRegistry()
metrics = MetricsRegistry(registry=custom_registry)

# Use it the same way
counter = metrics.counter('custom_counter')
counter.inc()

# Export metrics from this custom registry separately
output = generate_latest(custom_registry)
print(output.decode('utf-8'))
```

**Important**: The default behavior (when `registry=None`) uses the Instrumentator's registry, which means your metrics will automatically appear at `/api/v1/health/metrics` alongside the automatic HTTP metrics.

## Environment Variable Control

You can enable/disable metrics collection via environment variable:

```bash
# Enable metrics (default)
export ENABLE_METRICS=true

# Disable metrics
export ENABLE_METRICS=false
```

When disabled, the Instrumentator will not collect any metrics.

### With Namespace and Subsystem

```python
# This creates a metric named: fides_api_requests_total
counter = registry.counter(
    'requests_total',
    namespace='fides',
    subsystem='api'
)
```

## API Reference

### MetricsRegistry

#### Methods

- `counter(name, documentation="", labelnames=None, namespace="", subsystem="")` - Get or create a Counter
- `gauge(name, documentation="", labelnames=None, namespace="", subsystem="")` - Get or create a Gauge
- `histogram(name, documentation="", labelnames=None, buckets=None, namespace="", subsystem="")` - Get or create a Histogram
- `summary(name, documentation="", labelnames=None, namespace="", subsystem="")` - Get or create a Summary
- `clear()` - Clear all cached metrics (use with caution)

### Decorators

#### @count_calls

Count the number of times a function is called.

**Parameters:**
- `metric_name` (str, optional): Name for the counter. Defaults to `{function_name}_calls_total`
- `registry` (MetricsRegistry, optional): Registry to use. Defaults to global registry
- `labels` (dict, optional): Static labels to apply to the counter
- `namespace` (str): Optional namespace
- `subsystem` (str): Optional subsystem

#### @time_calls

Time the execution of a function.

**Parameters:**
- `metric_name` (str, optional): Name for the metric. Defaults to `{function_name}_duration_seconds`
- `registry` (MetricsRegistry, optional): Registry to use. Defaults to global registry
- `labels` (dict, optional): Static labels to apply to the metric
- `buckets` (list, optional): Bucket boundaries for histogram
- `namespace` (str): Optional namespace
- `subsystem` (str): Optional subsystem
- `use_histogram` (bool): If True, uses Histogram; if False, uses Summary. Default: True

#### @count_and_time

Both count calls and time execution.

**Parameters:**
- `metric_prefix` (str, optional): Prefix for metrics. Defaults to function name
- `registry` (MetricsRegistry, optional): Registry to use. Defaults to global registry
- `labels` (dict, optional): Static labels to apply to metrics
- `buckets` (list, optional): Bucket boundaries for histogram
- `namespace` (str): Optional namespace
- `subsystem` (str): Optional subsystem

Creates two metrics:
- `{metric_prefix}_calls_total` (Counter)
- `{metric_prefix}_duration_seconds` (Histogram)

## Examples

See `src/fides/api/metrics_example.py` for complete working examples.

## Testing

```bash
# Run the tests
pytest tests/api/test_metrics.py -v

# Run the integration example
python src/fides/api/metrics_integration_example.py

# View metrics endpoint (when server is running)
curl http://localhost:8080/api/v1/health/metrics
```

## Troubleshooting

### "Duplicated timeseries in CollectorRegistry" Error

**Cause**: The same metric is being registered multiple times, usually because:
1. The metric is being created with the same name but different labels
2. The application is being reloaded/restarted without clearing the registry (in development)
3. Multiple workers/processes are trying to register the same metric

**Solution**:
1. **Use consistent labels**: Always create metrics with the same labelnames
   ```python
   # Good - always use the same labels
   counter = registry.counter('requests', labelnames=['method', 'status'])
   counter.labels(method='GET', status='200').inc()

   # Bad - different labels for same metric
   counter1 = registry.counter('requests', labelnames=['method'])
   counter2 = registry.counter('requests', labelnames=['method', 'status'])  # Error!
   ```

2. **Use the MetricsRegistry**: It caches metrics globally to prevent duplicates
   ```python
   # Always use get_default_metrics_registry()
   registry = get_default_metrics_registry()
   counter = registry.counter('my_metric')  # Safe - will reuse existing
   ```

3. **Check if metric exists** before creating:
   ```python
   registry = get_default_metrics_registry()
   if not registry.has_metric('my_metric', namespace='fides'):
       counter = registry.counter('my_metric', namespace='fides')
   ```

4. **For development with hot reload**: Clear the global cache on app restart (not recommended for production)
   ```python
   # In development only!
   from fides.api.metrics import get_default_metrics_registry
   registry = get_default_metrics_registry()
   registry.clear()  # Clears global cache
   ```

### My metrics don't appear at /api/v1/health/metrics

**Cause**: You're using a custom CollectorRegistry instead of the Instrumentator's registry.

**Solution**: Either:
1. Don't pass a `registry` parameter (uses Instrumentator's registry): `MetricsRegistry()` or `get_default_metrics_registry()`
2. When using decorators, don't pass a custom registry: `@count_calls('my_metric')`

### Metrics are disabled

**Cause**: The `ENABLE_METRICS` environment variable is set to `false`.

**Solution**: Either:
1. Set `ENABLE_METRICS=true`
2. Don't set the variable (enabled by default)

### I see duplicate metric errors

**Cause**: Trying to create the same metric with different parameters (e.g., different labelnames).

**Solution**: The MetricsRegistry prevents this by caching metrics. If you get this error, you're likely creating metrics directly with prometheus_client instead of using MetricsRegistry.

### Metrics are not updating

**Cause**: You might be retrieving a different instance of the metric.

**Solution**: Always use the same MetricsRegistry instance, or use `get_default_metrics_registry()` consistently.

```python
# Good - consistent use of registry
registry = get_default_metrics_registry()
counter1 = registry.counter('requests')
counter2 = registry.counter('requests')  # Same instance
counter1.inc()  # counter2 also shows this increment

# Bad - creating new metrics directly
from prometheus_client import Counter
counter1 = Counter('requests', 'desc')  # Not using MetricsRegistry
counter2 = Counter('requests', 'desc')  # Error: metric already exists!
```

### HTTP metrics are not appearing

**Cause**: The Instrumentator might not be properly instrumented or the endpoint is excluded.

**Solution**:
1. Check that the Instrumentator is properly set up in `app_setup.py`
2. Verify your endpoint is not in the `excluded_handlers` list
3. Check that `ENABLE_METRICS` is not set to `false`

## Prometheus Scraping Configuration

To scrape metrics from Fides, add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'fides'
    scrape_interval: 15s
    static_configs:
      - targets: ['fides-server:8080']
    metrics_path: '/api/v1/health/metrics'
```
