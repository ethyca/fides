# Connection Types


## Available Connection Types

To view a list of all available connection types, visit `GET /api/v1/connection_type`.
This endpoint can be filtered with a `search` query param and is subject to change.  We include
database options and third party API services with which fidesops can communicate.

```json title="<code>GET /api/v1/connection_type</code>"
{
    "items": [
        {
            "identifier": "bigquery",
            "type": "database"
        },
        {
            "identifier": "mariadb",
            "type": "database"
        },
        {
            "identifier": "mongodb",
            "type": "database"
        },
        {
            "identifier": "mssql",
            "type": "database"
        },
        {
            "identifier": "mysql",
            "type": "database"
        },
        {
            "identifier": "postgres",
            "type": "database"
        },
        {
            "identifier": "redshift",
            "type": "database"
        },
        {
            "identifier": "snowflake",
            "type": "database"
        },
        {
            "identifier": "adobe_campaign",
            "type": "saas"
        },
        {
            "identifier": "auth0",
            "type": "saas"
        },
        {
            "identifier": "datadog",
            "type": "saas"
        },
        {
            "identifier": "hubspot",
            "type": "saas"
        },
        {
            "identifier": "logi_id",
            "type": "saas"
        },
        {
            "identifier": "mailchimp",
            "type": "saas"
        },
        {
            "identifier": "outreach",
            "type": "saas"
        },
        {
            "identifier": "salesforce",
            "type": "saas"
        },
        {
            "identifier": "segment",
            "type": "saas"
        },
        {
            "identifier": "sendgrid",
            "type": "saas"
        },
        {
            "identifier": "sentry",
            "type": "saas"
        },
        {
            "identifier": "stripe",
            "type": "saas"
        },
        {
            "identifier": "zendesk",
            "type": "saas"
        }
    ],
    "total": 21,
    "page": 1,
    "size": 50
}
```

## Required Connection Secrets

To view the secrets needed to authenticate with a given connection, visit `GET /api/v1/connection_type/<connection_type>/secret`.

### Example
```json title="<code>GET /api/v1/connection_type/sentry/secret</code>"
{
    "title": "sentry_schema",
    "description": "Sentry secrets schema",
    "type": "object",
    "properties": {
        "access_token": {
            "title": "Access Token",
            "type": "string"
        },
        "domain": {
            "title": "Domain",
            "default": "sentry.io",
            "type": "string"
        }
    },
    "required": [
        "access_token"
    ],
    "additionalProperties": false
}
```

## Setting up a SaaS Connector from a Template

To create all the resources necessary to set up a SaaS Connector in one request, you can create a connector from 
a template.

This creates a `saas` ConnectionConfig for you with your supplied name and description, with your supplied `secrets`.
In the example below, we're creating a `mailchimp` saas connector, so you should supply the relevant mailchimp `secrets`.
Your `instance_key` will become the identifier for the related `DatasetConfig` resource.  By default, the saas connection config
is enabled, with write access.


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

