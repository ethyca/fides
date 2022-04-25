
# Mailchimp

## Implementation Summary
You may use the following endpoints in Mailchimp to retrieve and delete Personally Identifiable Information (PII) when a user submits a Data Subject Request (DSR).

This table summarizes whether or not each available endpoint supports Right to Access and Right to Delete/Right to Forget 

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Messages](docs/link) | Yes/No | Yes/No |
|[Conversations](docs/link) | Yes/No | Yes/No |
|[Members](docs/link) | Yes/No | Yes/No |


## Connection Settings
To retrieve 

## Example SaaS Configuration
```yaml
saas_config:
  fides_key: mailchimp_connector_example
  name: Mailchimp SaaS Config
  description: A sample schema representing the Mailchimp connector for Fidesops
  version: 0.0.1

  connector_params:
    - name: domain
    - name: username
    - name: api_key

  client_config:
    protocol: https
    host:
      connector_param: domain
    authentication:
      strategy: basic_authentication
      configuration:
        username:
          connector_param: username
        password:
          connector_param: api_key

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