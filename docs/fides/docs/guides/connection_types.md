# Connection Types


## Available Connection Types

To view a list of all available connection types, visit `GET /api/v1/connection_type`.
This endpoint can be filtered with a `search` query param or a `system_type` query param 
and is subject to change.  We include database options and third party API services with 
which fidesops can communicate.

```json title="<code>GET /api/v1/connection_type</code>"
{
    "items": [
        {
            "identifier": "bigquery",
            "type": "database",
            "human_readable": "BigQuery"
        },
        {
            "identifier": "mariadb",
            "type": "database",
            "human_readable": "MariaDB"
        },
        {
            "identifier": "mongodb",
            "type": "database",
            "human_readable": "MongoDB"
        },
        {
            "identifier": "mssql",
            "type": "database",
            "human_readable": "Microsoft SQL Server"
        },
        {
            "identifier": "mysql",
            "type": "database",
            "human_readable": "MySQL"
        },
        {
            "identifier": "postgres",
            "type": "database",
            "human_readable": "PostgreSQL"
        },
        {
            "identifier": "redshift",
            "type": "database",
            "human_readable": "Amazon Redshift"
        },
        {
            "identifier": "snowflake",
            "type": "database",
            "human_readable": "Snowflake"
        },
        {
            "identifier": "adobe_campaign",
            "type": "saas",
            "human_readable": "Adobe Campaign"
        },
        {
            "identifier": "auth0",
            "type": "saas",
            "human_readable": "Auth0"
        },
        {
            "identifier": "datadog",
            "type": "saas",
            "human_readable": "Datadog"
        },
        {
            "identifier": "hubspot",
            "type": "saas",
            "human_readable": "HubSpot"
        },
        {
            "identifier": "mailchimp",
            "type": "saas",
            "human_readable": "Mailchimp"
        },
        {
            "identifier": "outreach",
            "type": "saas",
            "human_readable": "Outreach"
        },
        {
            "identifier": "salesforce",
            "type": "saas",
            "human_readable": "Salesforce"
        },
        {
            "identifier": "segment",
            "type": "saas",
            "human_readable": "Segment"
        },
        {
            "identifier": "sendgrid",
            "type": "saas",
            "human_readable": "SendGrid"
        },
        {
            "identifier": "sentry",
            "type": "saas",
            "human_readable": "Sentry"
        },
        {
            "identifier": "shopify",
            "type": "saas",
            "human_readable": "Shopify"
        },
        {
            "identifier": "stripe",
            "type": "saas",
            "human_readable": "Stripe"
        },
        {
            "identifier": "zendesk",
            "type": "saas",
            "human_readable": "Zendesk"
        },
        {
            "identifier": "manual_webhook",
            "type": "manual",
            "human_readable": "Manual Webhook"
        }
    ],
    "total": 23,
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

