# Connect to SQL and NoSQL Databases

## What is a Connection?

A _Connection_ links your owned databases and [third-party applications](../saas_connectors/saas_connectors.md) to Fides, allowing Fides to execute privacy requests against your collections and fields.

Fides currently supports connections to the following databases:

* PostgreSQL
* MongoDB
* MySQL
* MariaDB
* Microsoft SQLServer
* Amazon Redshift
* Snowflake
* Google BigQuery

Other platforms will be added in future releases.

## How do Connections differ from Datasets?

A Dataset is model of your database that describes the data contained within each field. A Connection stores the secrets to connect to the database. After Fides connects to your database, it dynamically generates queries to fulfil privacy requests by consulting the annotations in the Dataset.


## Create a new Connection 
The connection between Fides and your database is represented by a _Connection_. To create a new Connection, issue a request to the [Connection](./api/#operations-Connections-put_connections_api_v1_connection_put) endpoint, passing a payload that contains the properties listed below. 

| Field | Description |
| --- | --- |
| `name` | A human-readable name for your database. |
| `key` | A string token that uniquely identifies this Connection. If you don't supply a `key`, the `name` value, converted to snake-case, is used. |
| `connection-type` | Specifies the type of database. Valid values are `postgres`, `mongodb`, `mysql`, `mariadb`, `mssql`, `redshift`, `snowflake`, and `bigquery`. |
| `access` | The connection's permissions, either `read` (Fides may only read from your database) or `write` (Fides can read from and write to your database). |
| `disabled` | determines whether the Connection is active.  If `True`, Fides will skip running queries for any collection associated with that Connection. |
| `description` | _Optional._  An extra field to add further details about your Connection. |

While the Connection contains meta information about the database, it does not identify the database itself.

### Examples

All of the following are `PATCH` requests to `api/v1/connection`.

```json title="PostgreSQL"
[
  { 
    "name": "Application PostgreSQL DB",
    "key": "application_postgresql_db",
    "connection_type": "postgres",
    "access": "read"
  }
]
```

```json title="MongoDB"
[
  { 
    "name": "My Mongo DB",
    "key": "my_mongo_db",
    "connection_type": "mongodb",
    "access": "write",
    "disabled": false
  }
]
``` 

```json title="MySQL"
[
  { 
    "name": "My MySQL DB",
    "key": "my_mysql_db",
    "connection_type": "mysql",
    "access": "write",
    "disabled": false
  }
]
``` 

```json title="MariaDB"
[
  { 
    "name": "My Maria DB",
    "key": "my_maria_db",
    "connection_type": "mariadb",
    "access": "write",
    "disabled": false
  }
]
``` 

```json title="MsSQL""
[
  { 
    "name": "My MsSQL DB",
    "key": "my_mssql_db",
    "connection_type": "mssql",
    "access": "write",
    "disabled": false
  }
]
``` 

```json title="Manual Connections"
[
  {
    "name": "Manual connector",
    "key": "manual_connector",
    "connection_type": "manual",
    "access": "read",
    "disabled": false,
    "description": "Connector describing manual actions"
  }
]
``` 

## Set the Connection secrets
After creating a new Connection, you explain how to connect to it by setting its "secrets": the host, port, user, and password. These values are specific to each database, and should reference the user and password you would like Fides to use when accessing your database.

Call the [Connection Secrets](./api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put) endpoint. You can set the Connection attributes separately, or supply a single `url` string that encodes them all.

!!! Tip "Fides encrypts all Connection secrets values before they're stored."

### Set the secrets separately

This example sets the database secrets through separate properties and then tests the connection.

```json title="<code>PUT /api/v1/connection/application-postgresql-db/secret?verify=true</code>"
{
   "host": "host.docker.internal",
   "port": 5432,
   "dbname": "postgres_example",
   "username": "postgres",
   "password": "postgres"
}
```

### Set the secrets as a URL

This example sets the database secrets as a single `url` property, and skips the connection test.


```json title="<code>PUT api/v1/connection/my_mongo_db/secret?verify=false</code>" 
{
    "url": "mongodb://mongo_user:mongo_pass@mongodb_example/mongo_test"
}
```

### Examples
**Amazon Redshift**
```json title="<code>PUT api/v1/connection/my_redshift_db/secret</code>" 
{
    "url": "redshift+psycopg2://username@host.amazonaws.com:5439/database",
    "db_schema": "my_test_schema"
}
```

This Amazon Redshift example sets the database secrets using a `url` property and a `db_schema` property. Redshift
databases have one or more schemas, with the default being named `public`.  

If you need to use a different schema, specify a `db_schema` when setting your secrets, and it will be set as the `search_path` for querying.

**Google BigQuery**
```json title="<code>PUT api/v1/connection/my_bigquery_db/secret</code>"
{
    "dataset": "some-dataset",
    "keyfile_creds": {
        "type": "service_account",
        "project_id": "project-12345",
        "private_key_id": "qo28cy4nlwu",
        "private_key": "-----BEGIN PRIVATE KEY-----\nqi2unhflhncflkjas\nkqiu34c\n-----END PRIVATE KEY-----\n",
        "client_email": "something@project-12345.iam.gserviceaccount.com",
        "client_id": "287345028734538",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/something%40project-12345.iam.gserviceaccount.com"
    }
}
```

Google BigQuery requires two parameters: 

`dataset` - The name of your dataset. BigQuery datasets are top-level containers (within a project) that are used to organize and control access to your tables and views.

`keyfile_creds` - The credentials from your service account JSON keyfile, accessible for download from the GCP console.  


### Test your connection 
When setting your Connection secrets, setting the `verify` query parameter to `true` allows you to test the Connection by issuing a trivial request to the database. 

The `test_status` response property announces the test result as `succeeded` or `failed`. If the attempt has failed, the `failure_reason` property gives further details about the failure.

To skip the connection test, set `verify` to `false`.

You can verify that a Connection's secrets are valid at any time by calling the [Test a Connection's Secrets](./api#operations-Connections-test_connection_config_secrets_api_v1_connection__connection_key__test_get) endpoint:


```title="GET"
/api/v1/connection/application-postgresql-db/test
```
Test failures can be resolved by calling the [Set a Connection's Secrets](./api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put) endpoint, and resetting the secret values.

```json title="Success"
{
    "msg": "Test completed for ConnectionConfig with key: app_postgres_db.",
    "test_status": "succeeded",
    "failure_reason": null
}
```

```json title="Failure"
{
    "msg": "Secrets updated for ConnectionConfig with key: app_mongo_db.",
    "test_status": "failed",
    "failure_reason": "Operation Failure connecting to MongoDB."
}
```

## Associate a Dataset
Once you have a working Connection, it must be associated to an existing [dataset](datasets.md). This enables Fides to map and access the contents of your database. 

Call the `/dataset` endpoint with a JSON version of your dataset as the request body:

```json title="<code>PATCH /api/v1/connection/my_connection_key/dataset</code>"
[{
    "fides_key": "example_test_dataset",
    "name": "Example Test Dataset",
    "description": "Example of a dataset containing a variety of related tables like customers, products, addresses, etc.",
    "collections": [...]
}]
```

## Filtering your Connections

Fides can filter and return matching Connections based on the `connection_type`, the `testing_status`, the `system_status`, and whether the connection is `disabled`.

### Connection type filter

Including multiple `connection_type` query parameters and values will result in a query that looks for *any* connections with that type:

```json title="<code>GET api/v1//connection/?connection_type=mariadb&connection_type=postgres</code>"
{
    "items": [
        {
            "name": "Application Maria DB",
            "key": "app_mariadb_db",
            "description": null,
            "connection_type": "mariadb",
            "access": "write",
            "created_at": "2022-06-16T22:21:02.353226+00:00",
            "updated_at": "2022-06-16T22:21:02.353226+00:00",
            "disabled": false,
            "last_test_timestamp": null,
            "last_test_succeeded": null
        },
        {
            "name": "Application PostgreSQL DB",
            "key": "app_postgres_db",
            "description": "postgres backup",
            "connection_type": "postgres",
            "access": "write",
            "created_at": "2022-06-16T22:20:24.972539+00:00",
            "updated_at": "2022-06-16T22:20:24.972539+00:00",
            "disabled": false,
            "last_test_timestamp": null,
            "last_test_succeeded": null
        }
    ],
    "total": 2,
    "page": 1,
    "size": 50
}

```

### Disabled filter
The `disabled` filter will return datastores are skipped as part of privacy request execution:

```json title="<code>GET api/v1/connection/?disabled=true</code>"
{
    "items": [
        {
            "name": "My Mongo DB",
            "key": "app_mongo_db",
            "description": "Primary Mongo DB",
            "connection_type": "mongodb",
            "access": "write",
            "created_at": "2022-06-16T22:20:34.122212+00:00",
            "updated_at": "2022-06-16T22:20:34.122212+00:00",
            "disabled": true,
            "last_test_timestamp": null,
            "last_test_succeeded": null
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}

```

### Test_Status filter
The `test_status` filter queries on the status of the last successful test:

```json title="<code>GET api/v1/connection/?test_status=false</code>"
{
    "items": [
        {
            "name": "My Mongo DB",
            "key": "app_mongo_db",
            "description": "Primary Mongo DB",
            "connection_type": "mongodb",
            "access": "write",
            "created_at": "2022-06-16T22:20:34.122212+00:00",
            "updated_at": "2022-06-16T22:20:34.122212+00:00",
            "disabled": true,
            "last_test_timestamp": 2022-06-16T22:20:34.122212+00:00,
            "last_test_succeeded": false
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}

```

### System_Status filter
The `system_status` filter surfaces either `database` or [`saas`-type](../saas_connectors/saas_connectors.md) connectors:

```json title="<code>GET api/v1/connection/?system_type=database</code>"
{
    "items": [
        {
            "name": "My Mongo DB",
            "key": "app_mongo_db",
            "description": "Primary Mongo DB",
            "connection_type": "mongodb",
            "access": "write",
            "created_at": "2022-06-16T22:20:34.122212+00:00",
            "updated_at": "2022-06-16T22:20:34.122212+00:00",
            "disabled": true,
            "last_test_timestamp": 2022-06-16T22:20:34.122212+00:00,
            "last_test_succeeded": false
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}
```

## Search your Connections
You can search the `name`, `key`, and `description` fields of your Connections with the `search` query parameter.

```json title="<code>GET /api/v1/connection/?search=application mysql</code>"
{
    "items": [
        {
            "name": "Application MySQL DB",
            "key": "app_mysql_db",
            "description": "My Backup MySQL DB",
            "connection_type": "mysql",
            "access": "read",
            "created_at": "2022-06-13T18:03:28.404091+00:00",
            "updated_at": "2022-06-13T18:03:28.404091+00:00",
            "last_test_timestamp": null,
            "last_test_succeeded": null
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}
```


## View available connection types
To view a list of all available connection types, visit `GET /api/v1/connection_type`. This endpoint can be filtered with a `search` query parameter, and is subject to change.  Both database options and third party API services are included.

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

## View required connection secrets
To view the secrets needed to authenticate with a given connection, visit `GET /api/v1/connection_type/<connection_type>/secret`.

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