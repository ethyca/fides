# Connection Types


## Available Connection Types

To view a list of all available connection types, visit `/api/v1/connection_type`.
This endpoint can be filtered with a `search` query param and is subject to change.  We include
database options and third party API services with which Fidesops can communicate.

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
