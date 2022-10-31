
# Salesforce

## Implementation Summary

Fides uses the following Salesforce endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

For more information, see the [Salesforce sObject API reference](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_sobject_basic_info_post.htm).

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Query](https://developer.salesforce.com/docs/atlas.en-us.238.0.api_rest.meta/api_rest/resources_query.htm) | Yes | No |
|[Contact](https://developer.salesforce.com/docs/atlas.en-us.238.0.object_reference.meta/object_reference/sforce_api_objects_contact.htm) | Yes | Yes |
|[Case](https://developer.salesforce.com/docs/atlas.en-us.238.0.object_reference.meta/object_reference/sforce_api_objects_case.htm) | Yes | Yes |
|[Lead](https://developer.salesforce.com/docs/atlas.en-us.238.0.object_reference.meta/object_reference/sforce_api_objects_lead.htm) | Yes | Yes |
|[Account](https://developer.salesforce.com/docs/atlas.en-us.238.0.object_reference.meta/object_reference/sforce_api_objects_account.htm) | Yes | Yes |
|[CampaignMember](https://developer.salesforce.com/docs/atlas.en-us.238.0.object_reference.meta/object_reference/sforce_api_objects_campaignmember.htm) | Yes | Yes |

## Connection Settings

Fidesops provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give fidesops permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fidesops.toml` file is set to `false`.

## Example Salesforce Configuration

```yaml
saas_config:
  fides_key: salesforce_connector_example
  name: Salesforce SaaS Config
  type: salesforce
  description: A sample schema representing the Salesforce connector for Fidesops
  version: 0.0.1

  connector_params:
    - name: domain
    - name: username
    - name: password
    - name: client_id
    - name: client_secret
    - name: access_token

  client_config:
    protocol: https
    host: <domain>
    authentication:
      strategy: bearer
      configuration:
        token: <access_token>

  test_request:
    method: GET
    path: /services/data/v54.0/sobjects

  endpoints:
    - name: contact_list
      requests:
        read:
          method: GET
          path: /services/data/v54.0/query
          query_params:
            - name: q
              value: SELECT Id FROM Contact WHERE Email='<email>'
          param_values:
            - name: email
              identity: email
          data_path: records
    - name: contacts
      requests:
        read:
          method: GET
          path: /services/data/v54.0/sobjects/Contact/<contact_id>
          param_values:
            - name: contact_id
              references:
                - dataset: salesforce_connector_example
                  field: contact_list.Id
                  direction: from
        update:
          method: PATCH
          path: /services/data/v54.0/sobjects/Contact/<contact_id>
          body: |
            {
              <masked_object_fields>
            }
          param_values:
            - name: contact_id
              references:
                - dataset: salesforce_connector_example
                  field: contacts.Id
                  direction: from
    - name: case_list
      requests:
        read:
          method: GET
          path: /services/data/v54.0/query
          query_params:
            - name: q
              value: SELECT Id FROM Case WHERE ContactId='<contact_id>'
          param_values:
            - name: contact_id
              references:
                - dataset: salesforce_connector_example
                  field: contact_list.Id
                  direction: from
          data_path: records
    - name: cases
      requests:
        read:
          method: GET
          path: /services/data/v54.0/sobjects/Case/<case_id>
          param_values:
            - name: case_id
              references:
                - dataset: salesforce_connector_example
                  field: case_list.Id
                  direction: from
        update:
          method: PATCH
          path: /services/data/v54.0/sobjects/Case/<case_id>
          body: |
            {
              <masked_object_fields>
            }
          param_values:
            - name: case_id
              references:
                - dataset: salesforce_connector_example
                  field: cases.Id
                  direction: from
    - name: lead_list
      requests:
        read:
          method: GET
          path: /services/data/v54.0/query
          query_params:
            - name: q
              value: SELECT Id FROM Lead WHERE Email='<email>'
          param_values:
            - name: email
              identity: email
          data_path: records
    - name: leads
      requests:
        read:
          method: GET
          path: /services/data/v54.0/sobjects/Lead/<lead_id>
          param_values:
            - name: lead_id
              references:
                - dataset: salesforce_connector_example
                  field: lead_list.Id
                  direction: from
        update:
          method: PATCH
          path: /services/data/v54.0/sobjects/Lead/<lead_id>
          body: |
            {
              <masked_object_fields>
            }
          param_values:
            - name: lead_id
              references:
                - dataset: salesforce_connector_example
                  field: leads.Id
                  direction: from
    - name: accounts
      requests:
        read:
          method: GET
          path: /services/data/v54.0/sobjects/Account/<account_id>
          param_values:
            - name: account_id
              references:
                - dataset: salesforce_connector_example
                  field: contacts.AccountId
        update:
          method: PATCH
          path: /services/data/v54.0/sobjects/Account/<account_id>
          body: |
            {
              <masked_object_fields>
            }
          param_values:
            - name: account_id
              references:
                - dataset: salesforce_connector_example
                  field: accounts.Id
                  direction: from
    - name: campaign_member_list
      requests:
        read:
          method: GET
          path: /services/data/v54.0/query
          query_params:
            - name: q
              value: SELECT Id FROM CampaignMember WHERE Email='<email>'
          param_values:
            - name: email
              identity: email
          data_path: records
    - name: campaign_members
      requests:
        read:
          method: GET
          path: /services/data/v54.0/sobjects/CampaignMember/<campaign_member_id>
          param_values:
            - name: campaign_member_id
              references:
                - dataset: salesforce_connector_example
                  field: campaign_member_list.Id
                  direction: from
        update:
          method: PATCH
          path: /services/data/v54.0/sobjects/CampaignMember/<campaign_member_id>
          body: |
            {
              <masked_object_fields>
            }
          param_values:
            - name: campaign_member_id
              references:
                - dataset: salesforce_connector_example
                  field: campaign_members.Id
                  direction: from
```
