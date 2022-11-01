# Connect to SaaS Applications

## What is a SaaS connection?

A Fides SaaS (Software as a Service) Connection allows a user to connect to a third-party application (e.g., Mailchimp, Stripe, Slack, etc.), and execute data access and erasure requests against that application. Fides represents your SaaS connections as a [Dataset](../getting-started/datasets.md), accessed via a [Connection](../getting-started/database_connectors.md), and configured by a [SaaS config](./saas_config.md).

## Supported SaaS applications

The current implementation of the SaaS framework can support any SaaS application that uses these features:

- Basic auth, bearer auth, OAuth2 (Authorization Code Flow)
- Data access via HTTP requests
- Erasure via HTTP requests
- Pagination based on headers and response contents

The following features are planned for future releases and will allow for the configuration of broader types of connections:

- Custom Python functions for access and erasure requests
- Retry logic based on status codes and response contents

For full examples of supported Connections, see the [example configurations](./example_configs/adobe.md).

## Configure a SaaS connector

A SaaS Connector [Postman](../development/postman/using_postman.md) collection is available to execute the necessary steps to configure a SaaS connector. When running the Fides webserver, you may also navigate to the interactive API docs at `http://{server_url}/docs` (e.g., `http://0.0.0.0:8080/docs`) to access the following endpoints.

### Create a [Connection](../getting-started/database_connectors.md) of type `saas`

```json title="<code>PATCH api/v1/connection</code>"
[
  {
    "name": "SaaS Application",
    "key": {saas_key},
    "connection_type": "saas",
    "access": "read"
  }
]
```

### Add a SaaS Config (in JSON format)

```json title="<code>PATCH api/v1/connection/{saas_key}/saas_config</code>"
{
    "fides_key": "mailchimp_connector_example",
    "name": "Mailchimp SaaS Config",
    "type": "mailchimp",
    "description": "A sample schema representing the Mailchimp connector for fides"
    ...
```

### Configure your secrets

```json title="<coce>PUT api/v1/connection/{saas_key}/secret</code>"
{
  "domain": "{mailchimp_domain}",
  "username": "{mailchimp_username}",
  "api_key": "{mailchimp_api_key}"
}
```

### Add a Dataset (in JSON format)

```json title="<code>PUT api/v1/connection/{saas_key}/dataset</code>"
[
  {
    "fides_key":"mailchimp_connector_example",
    "name":"Mailchimp Dataset",
    "description":"A sample dataset representing the Mailchimp connector for fidesops",
    "collections":[
      {
        "name":"messages"
    ...
```

## Additional considerations

The following constraints are enforced by the API validation:

1. A SaaS connector dataset cannot have any `identities` or `references` in the `fidesops_meta`. These relationships must be defined in the [SaaS config](./saas_config.md).
2. SaaS config references can only have a direction of `from`.
3. The `fides_key` between the SaaS config and the Dataset must match in order to be associated.

## Set up a SaaS connector from a template

To create all the resources necessary to set up a SaaS Connector in one request, you can create a connector from
a template. This creates a `saas` Connection with your supplied name and description, using your supplied `secrets`.

The example below creates a [mailchimp](./example_configs/mailchimp.md) saas connector, and would need the relevant mailchimp `secrets`.

Your `instance_key` will become the identifier for the related [Dataset](../getting-started/datasets.md). By default, the saas connection config is enabled with write access.

```json title="<code>POST /connection/instantiate/mailchimp</code>"
{
    "name": "My Mailchimp connector",
    "description": "Production Mailchimp Instance",
    "secrets": {
        "domain": "{{mailchimp_domain}}",
        "api_key": "{{mailchimp_api_key}}",
        "username": "{{mailchimp_username}}"
    },
    "instance_key": "primary_mailchimp",
}
```
