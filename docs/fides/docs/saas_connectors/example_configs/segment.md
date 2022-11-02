
# Segment

## Implementation Summary
Fides uses the following Segment endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Users](https://segment.com/docs/personas/profile-api/#api-reference) | Yes | No |
|[Events](https://segment.com/docs/personas/profile-api/#api-reference) | Yes | No |
|[Traits](https://segment.com/docs/personas/profile-api/#api-reference) | Yes | No |
|[External IDs](https://segment.com/docs/personas/profile-api/#api-reference) | Yes | No |
|[Regulations](https://segment.com/docs/privacy/user-deletion-and-suppression/#overview) | Yes | Yes |

## Connection Settings
Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `false`. 

## Example Segment Configuration
```yaml
saas_config:
  fides_key: segment_connector_example
  name: Segment SaaS Config
  description: A sample schema representing the Segment connector for Fides
  version: 0.0.1

  connector_params:
    - name: domain
    - name: personas_domain
    - name: workspace
    - name: access_token
    - name: namespace_id
    - name: access_secret


  client_config:
    protocol: https
    host:
      connector_param: domain
    authentication:
      strategy: bearer_authentication
      configuration:
        token:
          connector_param: access_token

  test_request:
    method: GET
    path: /v1beta/workspaces/

  endpoints:
  - name: segment_user
    requests:
      read:
        method: GET
        path: /v1/spaces/<namespace_id>/collections/users/profiles/user_id:<user_id>/metadata
        param_values:
          - name: namespace_id
            connector_param: namespace_id
          - name: user_id
            identity: email
        client_config:
          protocol: https
          host:
            connector_param: personas_domain
          authentication:
            strategy: basic_authentication
            configuration:
              username:
                connector_param: access_secret
  - name: track_events
    requests:
      read:
        method: GET
        path: /v1/spaces/<namespace_id>/collections/users/profiles/<segment_id>/events
        param_values:
          - name: namespace_id
            connector_param: namespace_id
          - name: segment_id
            references:
              - dataset: segment_connector_example
                field: segment_user.segment_id
                direction: from
        data_path: data
        pagination:
          strategy: link
          configuration:
            source: body
            path: cursor.url
        client_config:
          protocol: https
          host:
            connector_param: personas_domain
          authentication:
            strategy: basic_authentication
            configuration:
              username:
                connector_param: access_secret
  - name: traits
    requests:
      read:
        method: GET
        path: /v1/spaces/<namespace_id>/collections/users/profiles/<segment_id>/traits
        query_params:
          - name: limit
            value: 17
        param_values:
          - name: namespace_id
            connector_param: namespace_id
          - name: segment_id
            references:
              - dataset: segment_connector_example
                field: segment_user.segment_id
                direction: from
        data_path: traits
        pagination:
          strategy: link
          configuration:
            source: body
            path: cursor.url
        client_config:
          protocol: https
          host:
            connector_param: personas_domain
          authentication:
            strategy: basic_authentication
            configuration:
              username:
                connector_param: access_secret
  - name: external_ids
    requests:
      read:
        method: GET
        path: /v1/spaces/<namespace_id>/collections/users/profiles/<segment_id>/external_ids
        param_values:
          - name: namespace_id
            connector_param: namespace_id
          - name: segment_id
            references:
              - dataset: segment_connector_example
                field: segment_user.segment_id
                direction: from
        data_path: data
        pagination:
          strategy: link
          configuration:
            source: body
            path: cursor.url
        client_config:
          protocol: https
          host:
            connector_param: personas_domain
          authentication:
            strategy: basic_authentication
            configuration:
              username:
                connector_param: access_secret

  data_protection_request:
    method: POST
    path: /v1beta/workspaces/<workspace_name>/regulations
    headers:
      - name: Content-Type
        value: application/json
    param_values:
      - name: workspace_name
        connector_param: workspace
      - name: user_id
        identity: email
    body: '{"regulation_type": "Suppress_With_Delete", "attributes": {"name": "userId", "values": ["<user_id>"]}}'
    client_config:
      protocol: https
      host:
        connector_param: domain
      authentication:
        strategy: bearer_authentication
        configuration:
          token:
            connector_param: access_token
```
