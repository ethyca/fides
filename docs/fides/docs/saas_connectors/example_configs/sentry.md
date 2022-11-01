# Sentry

## Implementation Summary

Fides uses the following Sentry endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Organizations](https://docs.sentry.io/api/organizations/list-your-organizations/) | Yes | No |
|[Users](https://docs.sentry.io/api/organizations/list-an-organizations-users/) | Yes | No |
|[Projects](https://docs.sentry.io/api/organizations/list-an-organizations-projects/) | Yes | Yes |
|[Issues](https://docs.sentry.io/api/events/list-a-projects-issues/) | Yes | No |
|[User Feedback](https://docs.sentry.io/api/projects/list-a-projects-user-feedback/) | Yes | No |

## Connection Settings

Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `false`.

## Example Sentry Configuration

```yaml
saas_config:
  fides_key: sentry_connector
  name: Sentry SaaS Config
  description: A sample schema representing the Sentry connector for Fides
  version: 0.0.1

  connector_params:
    - name: host
    - name: access_token

  client_config:
    protocol: https
    host:
      connector_param: host
    authentication:
      strategy: bearer_authentication
      configuration:
        token:
          connector_param: access_token

  test_request:
    method: GET
    path: /api/0/organizations/

  endpoints:
    - name: organizations
      requests:
        read:
          method: GET
          path: /api/0/organizations/
          param_values:
            - name: placeholder
              identity: email
          pagination:
            strategy: link
            configuration:
              source: headers
              rel: next
    - name: employees
      requests:
        read:
          method: GET
          path: /api/0/organizations/<organization_slug>/users/
          param_values:
            - name: organization_slug
              references:
                - dataset: sentry_connector
                  field: organizations.slug
                  direction: from
          postprocessors:
            - strategy: filter
              configuration:
                field: email
                value:
                  identity: email
    - name: projects
      requests:
        read:
          method: GET
          path: /api/0/projects/
          param_values:
            - name: placeholder
              identity: email
          pagination:
            strategy: link
            configuration:
              source: headers
              rel: next
    - name: issues
      requests:
        update:
          method: PUT
          path: /api/0/issues/<issue_id>/
          headers:
            - name: Content-Type
              value: application/json
          param_values:
            - name: issue_id
              references:
                - dataset: sentry_connector
                  field: issues.id
                  direction: from
          body: '{"assignedTo": ""}'
        read:
          method: GET
          path: /api/0/projects/<organization_slug>/<project_slug>/issues/
          grouped_inputs: [organization_slug, project_slug, query]
          query_params:
            - name: query
              value: assigned:<query>
          param_values:
            - name: organization_slug
              references:
                - dataset: sentry_connector
                  field: projects.organization.slug
                  direction: from
            - name: project_slug
              references:
                - dataset: sentry_connector
                  field: projects.slug
                  direction: from
            - name: query
              identity: email
          pagination:
            strategy: link
            configuration:
              source: headers
              rel: next
    - name: user_feedback
      requests:
        read:
          method: GET
          path: /api/0/projects/<organization_slug>/<project_slug>/user-feedback/
          grouped_inputs: [organization_slug, project_slug]
          param_values:
            - name: organization_slug
              references:
                - dataset: sentry_connector
                  field: projects.organization.slug
                  direction: from
            - name: project_slug
              references:
                - dataset: sentry_connector
                  field: projects.slug
                  direction: from
          postprocessors:
            - strategy: filter
              configuration:
                field: email
                value:
                  identity: email
          pagination:
            strategy: link
            configuration:
              source: headers
              rel: next
    - name: person
      after: [sentry_connector.projects]
      requests:
        read:
          method: GET
          ignore_errors: true
          path: /api/0/projects/<organization_slug>/<project_slug>/users/
          grouped_inputs: [organization_slug, project_slug, query]
          query_params:
            - name: query
              value: email:<query>
          param_values:
            - name: organization_slug
              references:
                - dataset: sentry_connector
                  field: projects.organization.slug
                  direction: from
            - name: project_slug
              references:
                - dataset: sentry_connector
                  field: projects.slug
                  direction: from
            - name: query
              identity: email
          pagination:
            strategy: link
            configuration:
              source: headers
              rel: next
```
