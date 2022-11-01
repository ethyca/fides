
# Adobe Campaign

## Implementation Summary

Fides uses the following Adobe Campaign endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Profile](https://experienceleague.adobe.com/docs/campaign-standard/using/working-with-apis/global-concepts/endpoints.html?lang=en) | Yes | Yes |
|[History](https://experienceleague.adobe.com/docs/campaign-standard/using/working-with-apis/global-concepts/endpoints.html?lang=en) | Yes | Yes |
|[Privacy Tool](https://experienceleague.adobe.com/docs/campaign-standard/using/working-with-apis/global-concepts/endpoints.html?lang=en) | Yes | Yes |

## Connection Settings

Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `false`.

## Example Adobe Configuration

```yaml
saas_config:
  fides_key: adobe_campaign_connector_example
  name: Adobe Campaign SaaS Config
  type: adobe_campaign
  description: A schema representing the Adobe Campaign connector for Fides
  version: 0.0.1

  connector_params:
    - name: domain
      default_value: mc.adobe.io
    - name: organization_id
    - name: namespace
      default_value: defaultNamespace1
      description: The namespace to use for data protections requests
    - name: regulation
      description: The regulation to follow for data protection requests
    - name: client_id
    - name: access_token

  client_config:
    protocol: https
    host: <domain>/<organization_id>
    authentication:
      strategy: bearer
      configuration:
        token: <access_token>

  test_request:
    method: GET
    path: /campaign/profileAndServices/profile/PKey
    headers:
      - name: X-Api-Key
        value: <client_id>
    query_params:
      - name: _lineCount
        value: 1
    param_values:
      - name: client_id
        connector_param: client_id

  endpoints:
    - name: profile
      requests:
        read:
          method: GET
          path: /campaign/profileAndServices/profile/byEmail
          headers:
            - name: X-Api-Key
              value: <client_id>
          query_params:
            - name: email
              value: <email>
          param_values:
            - name: client_id
              connector_param: client_id
            - name: email
              identity: email
          data_path: content
    - name: marketing_history
      requests:
        read:
          method: GET
          path: /campaign/profileAndServices/history/byEmail
          headers:
            - name: X-Api-Key
              value: <client_id>
          query_params:
            - name: email
              value: <email>
          param_values:
            - name: client_id
              connector_param: client_id
            - name: email
              identity: email
          data_path: content

  data_protection_request:
    method: POST
    path: /campaign/privacy/privacyTool
    headers:
      - name: X-Api-Key
        value: <client_id>
    param_values:
      - name: client_id
        connector_param: client_id
      - name: regulation
        connector_param: regulation
      - name: namespace
        connector_param: namespace
      - name: reconciliation_value
        identity: email
    body: |
      {
          "name": "<privacy_request_id>",
          "namespaceName": "<namespace>",
          "reconciliationValue": "<reconciliation_value>",
          "regulation": "<regulation>",
          "label": "Erasure Request",
          "type": "delete"
      }
```
