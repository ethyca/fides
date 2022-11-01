
# Sendgrid

## Implementation Summary

Fides uses the following Sendgrid endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Contacts](https://docs.sendgrid.com/api-reference/contacts/search-contacts) | Yes | Yes |

## Connection Settings

Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `fALSE`.

## Example Sendgrid Configuration

```yaml
saas_config:
  fides_key: sendgrid_connector_example
  name: Sendgrid SaaS Config
  type: sendgrid
  description: A sample schema representing the Sendgrid connector for Fides
  version: 0.0.1

  connector_params:
    - name: domain
    - name: api_key

  client_config:
    protocol: https
    host: <domain>
    authentication:
      strategy: bearer
      configuration:
        token: <api_key>

  test_request:
    method: GET
    path: /v3/marketing/contacts

  endpoints:
    - name: contacts
      requests:
        read:
          method: POST
          path: /v3/marketing/contacts/search
          body: |
            {
              "query": "email = '<email>'"
            }
          param_values:
            - name: email
              identity: email
          data_path: result
        delete:
          method: DELETE
          path: /v3/marketing/contacts?ids=<contact_id>
          param_values:
            - name: contact_id
              references:
                - dataset: sendgrid_connector_example
                  field: contacts.id
                  direction: from
```
