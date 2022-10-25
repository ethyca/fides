# SaaS Rate limiting

Rate limits can be used to limit how fast requests can be made to saas endpoints. 

A rate limit configuration can be set the within the client config for saas connectors. It can also be set within endpoint request config to override the config for specific endpoints. 

## Configuration details
- `enabled` (_bool_): *Optional.* Determines if the rate limiter is enabled.
- `limits` (_list([RateLimit](#rate-limit-configuration))_): *Optional.* A list of RateLimit objects which can definte multiple rate limits for endpoint requests.

### Rate Limit 
- `rate` (_int_): Number of calls which are allow for the specified period
- `period` (_str_): The time period for which to limit calls. Allows values are `second`, `minute`, `hour`, `day`.

## Implementation details

## Examples
