# Connect to SaaS Applications

## What is a SaaS connection?

<<<<<<< HEAD:docs/fides/docs/saas_connectors/saas_connectors.md
A Fides SaaS (Software as a Service) Connection allows a user to connect to a third-party application (e.g., Mailchimp, Stripe, Slack, etc.), and execute data access and erasure requests against that application. Fides represents your SaaS connections as a [Dataset](../getting-started/datasets.md), accessed via a [Connection](../getting-started/database_connectors.md), and configured by a [SaaS config](./saas_config.md).
=======
A SaaS (Software as a Service) connection is a connection type within fidesops that allows a user to connect to a SaaS application (e.g., Mailchimp, Stripe, Slack, etc.) and execute data access and erasure requests against that application. These connections use functionality introduced in earlier sections ([ConnectionConfigs](/guides/database_connectors.md#creating-a-connectionconfig-object) and [Datasets](/guides/datasets.md)) but also use a new [SaaS configuration](saas_config.md) specification to define how to connect to specific SaaS applications.
>>>>>>> unified-fides-2:docs/fidesops/docs/saas_connectors/saas_connectors.md

## Supported SaaS applications

The current implementation of the SaaS framework can support any SaaS application that uses these features:

- Basic auth, bearer auth, OAuth2 (Authorization Code Flow)
- Data access via HTTP requests
- Erasure via HTTP requests
- Pagination based on headers and response contents

The following features are planned for future releases and will allow for the configuration of broader types of connections:

- Custom Python functions for access and erasure requests
- Retry logic based on status codes and response contents

<<<<<<< HEAD:docs/fides/docs/saas_connectors/saas_connectors.md
For full examples of supported Connections, see the [example configurations](./example_configs/adobe.md).

## Configure a SaaS connector

A SaaS Connector [Postman](../development/postman/using_postman.md) collection is available to execute the necessary steps to configure a SaaS connector. When running the Fides webserver, you may also navigate to the interactive API docs at `http://{server_url}/docs` (e.g., `http://0.0.0.0:8080/docs`) to access the following endpoints.

### Create a [Connection](../getting-started/database_connectors.md) of type `saas`

```json title="<code>PATCH api/v1/connection</code>"
=======
Full [examples](https://github.com/ethyca/fidesops/tree/main/data/saas) of a valid SaaS config and Dataset are currently available for Mailchimp.

## How to configure a SaaS connector

For convenience we've included a SaaS Connector [Postman](../postman/using_postman.md) collection to execute the necessary steps to configure a SaaS connector.

1. Create a ConnectionConfig of type `saas`
```
PATCH api/v1/connection

>>>>>>> unified-fides-2:docs/fidesops/docs/saas_connectors/saas_connectors.md
[
  {
    "name": "SaaS Application",
    "key": {saas_key},
    "connection_type": "saas",
    "access": "read"
  }
]
```
<<<<<<< HEAD:docs/fides/docs/saas_connectors/saas_connectors.md

### Add a SaaS Config (in JSON format)

```json title="<code>PATCH api/v1/connection/{saas_key}/saas_config</code>"
=======
2. Add a SaaS Config (in JSON format)
```
PATCH api/v1/connection/{saas_key}/saas_config

>>>>>>> unified-fides-2:docs/fidesops/docs/saas_connectors/saas_connectors.md
{
    "fides_key": "mailchimp_connector_example",
    "name": "Mailchimp SaaS Config",
    "type": "mailchimp",
<<<<<<< HEAD:docs/fides/docs/saas_connectors/saas_connectors.md
    "description": "A sample schema representing the Mailchimp connector for fides"
    ...
```

### Configure your secrets

```json title="<coce>PUT api/v1/connection/{saas_key}/secret</code>"
=======
    "description": "A sample schema representing the Mailchimp connector for fidesops"
    ...
```
3. Configure the secrets. The SaaS config must already defined to provide validation for the secrets.
```
PUT api/v1/connection/{saas_key}/secret

>>>>>>> unified-fides-2:docs/fidesops/docs/saas_connectors/saas_connectors.md
{
  "domain": "{mailchimp_domain}",
  "username": "{mailchimp_username}",
  "api_key": "{mailchimp_api_key}"
}
```
<<<<<<< HEAD:docs/fides/docs/saas_connectors/saas_connectors.md

### Add a Dataset (in JSON format)

```json title="<code>PUT api/v1/connection/{saas_key}/dataset</code>"
=======
4. Add a Dataset (in JSON format)
```
PUT api/v1/connection/{saas_key}/dataset
>>>>>>> unified-fides-2:docs/fidesops/docs/saas_connectors/saas_connectors.md
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
<<<<<<< HEAD:docs/fides/docs/saas_connectors/saas_connectors.md
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

=======
These are constraints enforced by the API validation but it is important to keep these in mind.

1. A SaaS connector dataset cannot have any `identities` or `references` in the `fidesops_meta`. These relationships must be defined in the SaaS config.
2. SaaS config references can only have a direction of `from`.
3. The `fides_key` between the SaaS config and the Dataset must match. This is how we associate the two pieces together.
>>>>>>> unified-fides-2:docs/fidesops/docs/saas_connectors/saas_connectors.md
