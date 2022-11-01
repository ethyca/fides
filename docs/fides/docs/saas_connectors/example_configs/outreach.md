
# Outreach

## Implementation Summary

Fides uses the following Outreach endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Prospects](https://api.outreach.io/api/v2/docs#manage-prospects-and-accounts) | Yes | Yes |
|[Recipients](https://api.outreach.io/api/v2/docs#recipient) | Yes | Yes |

## Connection Settings

Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `false`.

## Example Outreach Configuration

```yaml
saas_config:
  fides_key: outreach_connector_example
  name: Outreach Example Config
  type: outreach
  description: A sample schema representing the Outreach connector for Fides
  version: 0.0.1

  connector_params:
    - name: domain
      default_value: platform.segmentapis.com
    - name: requester_email
      description: The email of the Outreach user to associate with each automated compliance request (data_protection_request)
    - name: client_id
    - name: client_secret
    - name: redirect_uri
    - name: page_size
      description: The number of entries to return per page

  client_config:
    protocol: https
    host: <domain>
    authentication:
      strategy: oauth2_authorization_code
      configuration:
        authorization_request:
          method: GET
          path: /auth/authorize
          query_params:
            - name: client_id
              value: <client_id>
            - name: redirect_uri
              value: <redirect_uri>
            - name: response_type
              value: code
            - name: scope
              value: prospects.all recipients.all teams.all roles.all accounts.all audits.all callDispositions.all callPurposes.all calls.all complianceRequests.all contentCategories.all contentCategoryMemberships.all contentCategoryOwnerships.all duties.all emailAddresses.all events.all favorites.all mailAliases.all mailboxes.all mailings.all opportunities.all opportunityProspectRoles.all opportunityStages.all personas.all phoneNumbers.all profiles.all rulesets.all sequenceStates.all sequenceSteps.all sequenceTemplates.all sequences.all snippets.all stages.all taskPriorities.all tasks.all templates.all users.all webhooks.all
            - name: state
              value: <state>
        token_request:
          method: POST
          path: /oauth/token
          headers:
            - name: Content-Type
              value: application/x-www-form-urlencoded
          query_params:
            - name: client_id
              value: <client_id>
            - name: client_secret
              value: <client_secret>
            - name: grant_type
              value: authorization_code
            - name: code
              value: <code>
            - name: redirect_uri
              value: <redirect_uri>
        refresh_request:
          method: POST
          path: /oauth/token
          headers:
            - name: Content-Type
              value: application/x-www-form-urlencoded
          query_params:
            - name: client_id
              value: <client_id>
            - name: client_secret
              value: <client_secret>
            - name: redirect_uri
              value: <redirect_uri>
            - name: grant_type
              value: refresh_token
            - name: refresh_token
              value: <refresh_token>

  test_request:
    method: GET
    path: /api/v2/roles

  endpoints:
    - name: prospects
      requests:
        read:
          method: GET
          path: /api/v2/prospects
          query_params:
            - name: filter[emails]
              value: <email>
          param_values:
            - name: email
              identity: email
          data_path: data
        delete:
          method: POST
          path: /api/v2/complianceRequests
          param_values:
            - name: requester_email
              connector_param: requester_email
            - name: email
              identity: email
          body: |
            {
              "data": {
                "type": "complianceRequest",
                "attributes": {
                  "requester_email": "<requester_email>",
                  "request_type": "Delete",
                  "object_type": "Prospect",
                  "request_object_email": "<email>"
                }
              }
            }
    - name: recipients
      requests:
        read:
          method: GET
          path: /api/v2/recipients
          query_params:
            - name: page[size]
              value: <page_size>
          param_values:
            - name: page_size
              connector_param: page_size
            - name: placeholder
              identity: email
          data_path: data
          pagination:
            strategy: link
            configuration:
              source: body
              path: links.next
          postprocessors:
            - strategy: filter
              configuration:
                field: attributes.value
                value:
                  identity: email
                exact: False
                case_sensitive: False
        delete:
          method: POST
          path: /api/v2/complianceRequests
          param_values:
            - name: requester_email
              connector_param: requester_email
            - name: email
              identity: email
          body: |
            {
              "data": {
                "type": "complianceRequest",
                "attributes": {
                  "requester_email": "<requester_email>",
                  "request_type": "Delete",
                  "object_type": "Recipient",
                  "request_object_email": "<email>"
                }
              }
            }
```
