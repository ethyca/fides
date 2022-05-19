# How-To: Connect to SaaS Applications

## What is a SaaS connection?

A SaaS (Software as a Service) connection is a connection type within Fidesops that allows a user to connect to a SaaS application (e.g., Mailchimp, Stripe, Slack, etc.) and execute data access and erasure requests against that application. These connections use functionality introduced in earlier sections ([ConnectionConfigs](/guides/database_connectors.md#creating-a-connectionconfig-object) and [Datasets](/guides/datasets.md)) but also use a new [SaaS configuration](saas_config.md) specification to define how to connect to specific SaaS applications.

## Supported SaaS applications

The current implementation of the SaaS framework can support any SaaS application that uses these features:

- Basic and bearer authentication
- Data access via HTTP GET requests
- Erasure via HTTP PUT requests

The following features are planned for future releases and will allow for the configuration of broader types of connections:

- OAuth 2.0 authentication
- Pagination based on headers and response contents
- Retry logic based on status codes and response contents

Full [examples](https://github.com/ethyca/fidesops/tree/main/data/saas) of a valid SaaS config and Dataset are currently available for Mailchimp.

## How to configure a SaaS connector

For convenience we've included a SaaS Connector [Postman](../postman/using_postman.md) collection to execute the necessary steps to configure a SaaS connector.

1. Create a ConnectionConfig of type `saas`
```
PATCH api/v1/connection

[
  {
    "name": "SaaS Application",
    "key": {saas_key},
    "connection_type": "saas",
    "access": "read"
  }
]
```
2. Add a SaaS Config (in JSON format)
```
PATCH api/v1/connection/{saas_key}/saas_config

{
    "fides_key": "mailchimp_connector_example",
    "name": "Mailchimp SaaS Config",
    "description": "A sample schema representing the Mailchimp connector for Fidesops"
    ...
```
3. Configure the secrets. The SaaS config must already defined to provide validation for the secrets.
```
PUT api/v1/connection/{saas_key}/secret?verify=true

{
  "domain": "{mailchimp_domain}",
  "username": "{mailchimp_username}",
  "api_key": "{mailchimp_api_key}"
}
```
4. Add a Dataset (in JSON format)
```
PUT api/v1/connection/{saas_key}/dataset
[
  {
    "fides_key":"mailchimp_connector_example",
    "name":"Mailchimp Dataset",
    "description":"A sample dataset representing the Mailchimp connector for Fidesops",
    "collections":[
      {
        "name":"messages"
    ...
```

## Additional considerations
These are constraints enforced by the API validation but it is important to keep these in mind.

1. A SaaS connector dataset cannot have any `identities` or `references` in the `fidesops_meta`. These relationships must be defined in the SaaS config.
2. SaaS config references can only have a direction of `from`.
3. The `fides_key` between the SaaS config and the Dataset must match. This is how we associate the two pieces together.