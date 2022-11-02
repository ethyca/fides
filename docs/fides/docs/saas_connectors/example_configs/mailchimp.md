# Mailchimp

## Implementation Summary

Fides uses the following Mailchimp endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Messages](https://mailchimp.com/developer/marketing/api/conversation-messages/list-messages/) | Yes | No |
|[Conversations](https://mailchimp.com/developer/marketing/api/conversation-messages/) | Yes | No |
|[Members](https://mailchimp.com/developer/marketing/api/list-members/get-member-info/) | Yes | Yes |

## Connection Settings

Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `false`.

## Example Mailchimp Configuration

```yaml
saas_config:
  fides_key: mailchimp_connector_example
  name: Mailchimp SaaS Config
  description: A sample schema representing the Mailchimp connector for Fides
  version: 0.0.1

  connector_params:
    - name: domain
    - name: username
    - name: api_key

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
    path: /3.0/lists

  endpoints:
  - name: messages
    requests:
      read:
        method: GET
        path: /3.0/conversations/<conversation_id>/messages
        param_values:
          - name: conversation_id
            references:
              - dataset: mailchimp_connector_example
                field: conversations.id
                direction: from
        data_path: conversation_messages
        postprocessors:
          - strategy: filter
            configuration:
              field: from_email
              value:
                identity: email
  - name: conversations
    requests:
      read:
        method: GET
        path: /3.0/conversations
        query_params:
          - name: count
            value: 1000
          - name: offset
            value: 0
        param_values:
          - name: placeholder
            identity: email
        data_path: conversations
        pagination:
          strategy: offset
          configuration:
            incremental_param: offset
            increment_by: 1000
            limit: 10000
  - name: member
    requests:
      read:
        method: GET
        path: /3.0/search-members
        query_params:
          - name: query
            value: <email>
        param_values:
          - name: email
            identity: email
        data_path: exact_matches.members
      update:
        method: PUT
        path: /3.0/lists/<list_id>/members/<subscriber_hash>
        param_values:
          - name: list_id
            references:
              - dataset: mailchimp_connector_example
                field: member.list_id
                direction: from
          - name: subscriber_hash
            references:
              - dataset: mailchimp_connector_example
                field: member.id
                direction: from
```
