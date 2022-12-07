
# Zendesk

## Implementation Summary

Fides uses the following Zendesk endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Search](https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/) | Yes | No |
|[Identities](https://developer.zendesk.com/api-reference/ticketing/users/user_identities/) | Yes | No |
|[Tickets](https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/) | Yes | Yes |
|[Ticket Comments](https://developer.zendesk.com/api-reference/ticketing/tickets/ticket_comments/) | Yes | Yes |

## Connection Settings

Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `false`.

## Example Zendesk Configuration

```yaml
saas_config:
  fides_key: zendesk_connector_example
  name: Zendesk SaaS Config
  type: zendesk
  description: A sample schema representing the Zendesk connector for Fides
  version: 0.0.1

  connector_params:
    - name: domain
    - name: username
    - name: api_key
    - name: page_size

  client_config:
    protocol: https
    host: <domain>
    authentication:
      strategy: basic
      configuration:
        username: <username>
        password: <api_key>

  test_request:
    method: GET
    path: /api/v2/users/search.json
    query_params:
      - name: query
        value: test@ethyca

  endpoints:
    - name: users
      requests:
        read:
          method: GET
          path: /api/v2/users/search.json
          query_params:
            - name: query
              value: <email>
          param_values:
            - name: email
              identity: email
          data_path: users
        delete:
          method: DELETE
          path: /api/v2/users/<user_id>.json
          param_values:
            - name: user_id
              references:
                - dataset: zendesk_connector_example
                  field: users.id
                  direction: from
    - name: user_identities
      requests:
        read:
          method: GET
          path: /api/v2/users/<user_id>/identities.json
          query_params:
            - name: page[size]
              value: <page_size>
          param_values:
            - name: user_id
              references:
                - dataset: zendesk_connector_example
                  field: users.id
                  direction: from
            - name: page_size
              connector_param: page_size
          data_path: identities
          pagination:
            strategy: link
            configuration:
              source: body
              path: links.next
    - name: tickets
      requests:
        read:
          method: GET
          path: /api/v2/users/<user_id>/tickets/requested.json
          query_params:
            - name: page[size]
              value: <page_size>
          param_values:
            - name: user_id
              references:
                - dataset: zendesk_connector_example
                  field: users.id
                  direction: from
            - name: page_size
              connector_param: page_size
          data_path: tickets
          pagination:
            strategy: link
            configuration:
              source: body
              path: links.next
        delete:
          method: DELETE
          path: /api/v2/tickets/<ticket_id>.json
          param_values:
            - name: ticket_id
              references:
                - dataset: zendesk_connector_example
                  field: tickets.id
                  direction: from
    - name: ticket_comments
      requests:
        read:
          method: GET
          path: /api/v2/tickets/<ticket_id>/comments.json
          query_params:
            - name: page[size]
              value: <page_size>
          param_values:
            - name: ticket_id
              references:
                - dataset: zendesk_connector_example
                  field: tickets.id
                  direction: from
            - name: page_size
              connector_param: page_size
          data_path: comments
          pagination:
            strategy: link
            configuration:
              source: body
              path: links.next
```
