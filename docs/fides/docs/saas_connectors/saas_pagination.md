# SaaS Pagination

These pagination strategies allow Fides to incrementally retrieve content from SaaS APIs. APIs can vary in the way subsequent pages are accessed so these configurable options aim to cover a majority of common use cases.

## Supported strategies
- `offset`: Iterates through the available pages by incrementing the value of a query param.
- `link`: Uses links returned in the headers or the body to get to the next page.
- `cursor`: Uses a value from the last-retrieved object to use as a query param pointing to the next set of results.

### Offset
This strategy can be used to iterate through pages, or to define the offset for a batch of results. In either case, this strategy increments the specified query param by the `increment_by` value until no more results are returned or the `limit` is reached.

#### Configuration details
- `incremental_param` (_str_): The query param to increment the value for.
- `increment_by` (_int_): The value to increment the `incremental_param` after each set of results.
- `limit` (optional _str_): The max value the `incremental_param` can reach.

#### Example
This example would take the `page` query param and increment it by 1 until the limit of 10 is reached or no more results are returned (whichever comes first).
```yaml
pagination:
  strategy: offset
  configuration:
    incremental_param: page
    increment_by: 1
    limit: 10
```

### Link
This strategy is used when the link to the next page is provided as part of the API response. The link is read from the headers or the body and used to get the next page of results.

#### Configuration details
- `source` (_str_): The location to get the link from, can be either `headers` or `body`.
- `path` (_str_): The expression used to refer to the location of the link within the headers or the body.

#### Examples
The source value of `headers` is meant to be used with responses following [RFC 5988](https://datatracker.ietf.org/doc/html/rfc5988#page-6).
```
Link: <https://api.host.com/conversations?page_ref=ad6f38r3>; rel="next",
      <https://api.host.com/conversations?page_ref=gss8ap4g>; rel="prev"
```
Given this Link header, we can specify a rel of `next` (case-insensitive). This indicates that we are looking in the `Link` header with a `rel` of next.
```yaml
pagination:
  strategy: link
  configuration:
    source: headers
    rel: next
```

We can also access links returned in the body. If we receive this value in the body:
```json
{
  ...
  "next_page": {
      "url": "https://api.host.com/conversations?page_ref=ad6f38r3"
  }
  ...
}
```
We can use the path value of `next_page.url` as the expression to access the url.
```yaml
pagination:
  strategy: link
  configuration:
    source: body
    path: next_page.url
```

### Cursor
This strategy is used when a specific value from a response object is used as a cursor to determine the starting point for the next set of results.

#### Configuration Details
- `cursor_param` (_str_): The name of the query param to assign the cursor value to.
- `field` (_str_): The field to read from the most recently retrieved object to use as the cursor value.

#### Examples
If an API request returns the following:
```json
{
  "messages": [
      {"id": 1, "msg": "this is"},
      {"id": 2, "msg": "a"}
      {"id": 3, "msg": "test"}
  ]
}
```
This strategy will take the field `id` from the last item returned and generate a new request with a query param of `after=3`
```yaml
pagination:
  strategy: cursor
  configuration:
    cursor_param: after
    field: id
```
