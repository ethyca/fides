# SaaS Rate limiting

Rate limits can be used to limit how fast requests can be made to saas endpoints. Rate limiting works accross Fides instances that share a Redis cluster. 

A rate limit configuration can be set the within the client config for saas connectors. It can also be set within endpoint request config to override the config for specific endpoints. 

## Configuration details
- `enabled` (_bool_): *Optional.* Determines if the rate limiter is enabled. Default is true.
- `limits` (_list([RateLimit](#rate-limit-configuration))_): *Optional.* A list of RateLimit objects which can definte multiple rate limits for endpoint requests.

### Rate Limit 
- `rate` (_int_): Number of calls which are allow for the specified period
- `period` (_str_): The time period for which to limit calls. Allows values are `second`, `minute`, `hour`, `day`.
- `custom_key` (_str_): *Optional.* An optional key which can be used to group rate usage accross endpoints or connectors. 

## Implementation details

Fides implements rate limiting as a fixed window algorithm. Epoch seconds are divided into discrete buckets based on the configured period. 

## Examples

### Limiting Connector

In this example we limit our connector to 10 TPS for all endpoints
```yaml
saas_config:
  fides_key: my_connector

rate_limit_config:
    limits:
    - rate: 10
      period: second
```

### Disable Limit For Specific Endpoint

In this example we limit our connector request rate but disable the limiter for `my_non_limited_entity` read requests.

```yaml
saas_config:
  fides_key: my_connector

  rate_limit_config:
    limits:
    - rate: 10
      period: second

  endpoints:
  - name: my_non_limited_entity
    requests:
      read:
        rate_limit_config:
          enabled: false

```

### Shared Rate Usage Accross Connectors

In this example `my_connector_1` and `my_connector_2` both contribute requests to the same time window as they share the custom key `shared_custom_key`.


```yaml
saas_config:
  fides_key: my_connector_1

rate_limit_config:
    limits:
    - rate: 10
      period: second
      custom_key: shared_custom_key

  fides_key: my_connector_2

rate_limit_config:
    limits:
    - rate: 10
      period: second
      custom_key: shared_custom_key
```
