# Connection Types


## Available Connection Types

To view a list of all available connection types, visit `GET /api/v1/connection_type`.
This endpoint can be filtered with a `search` query param and is subject to change.  We include
database options and third party API services with which fidesops can communicate.

```json title="<code>GET /api/v1/connection_type</code>"
{
    "items": [
        "bigquery",
        "hubspot",
        "mailchimp",
        "mariadb",
        "mongodb",
        "mssql",
        "mysql",
        "outreach",
        "postgres",
        "redshift",
        "salesforce",
        "segment",
        "sentry",
        "snowflake",
        "stripe",
        "zendesk"
    ],
    "total": 15,
    "page": 1,
    "size": 50
}
```

## Required Connection Secrets

To view the secrets needed to authenticate with a given connection, visit `GET /api/v1/connection_type/<connection_type>/secret`.

### Example
```json title="<code>GET /api/v1/connection_type/sentry/secret</code>"
{
    "title": "sentry_connector_schema",
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