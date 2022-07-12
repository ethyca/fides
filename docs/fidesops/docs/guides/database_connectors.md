# Connect to SQL and NoSQL Databases

## What is a connection?

A _connection_ links your databases to fidesops, so you can gather and update selected PII 
categories.

## Supported databases

Fidesops supports connections to the following databases:

* PostgreSQL
* MongoDB
* MySQL
* MariaDB
* Microsoft SQLServer
* Amazon Redshift
* Snowflake
* Google BigQuery

Other platforms will be added in future releases.

## Create a ConnectionConfig object 

The connection between fidesops and your database is represented by a _ConnectionConfig_ object. To create a ConnectionConfig, you issue a request to the [Create a ConnectionConfig](/fidesops/api/#operations-Connections-put_connections_api_v1_connection_put) operation, passing a payload that contains the properties listed below. 

* `name`  is a human-readable name for your database.

* `key`  is a string token that uniquely identifies your ConnectionConfig object. If you don't supply a `key`, the `name` value, converted to snake-case, is used. For example, if the `name` is `Application PostgreSQL DB`, the converted key is `application_postgresql_db`.

* `connection-type` specifies the type of database. Valid values are `postgres`, `mongodb`, `mysql`, `mariadb`, `mssql`, `redshift`, `snowflake`, and `bigquery`.

* `access` sets the connection's permissions, one of "read" (fidesops may only read from your database) or "write" (fidesops can read from and write to your database).

* `disabled` determines whether the ConnectionConfig is active.  If True, we skip running queries for any collection associated with that ConnectionConfig.

* `description` is an extra field to add further details about your connection. 

While the ConnectionConfig object contains meta information about the database, you'll notice that it doesn't actually identify the database itself. We'll get to that when we set the ConnectionConfig's "secrets".


### PostgreSQL

```json title="<code>PATCH api/v1/connection</code>"
[
  { 
    "name": "Application PostgreSQL DB",
    "key": "application_postgresql_db",
    "connection_type": "postgres",
    "access": "read"
  }
]
```

### MongoDB

```json title="<code>PATCH api/v1/connection</code>"
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

### MySQL 

```json title="<code>PATCH api/v1/connection</code>"
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

### MariaDB

```json title="<code>PATCH api/v1/connection</code>"
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

### MsSQL

```json title="<code>PATCH api/v1/connection </code>"
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

### Manual connections

```json title="<code>PATCH api/v1/connection </code>"
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

## Set ConnectionConfig secrets

After you create a ConnectionConfig, you explain how to connect to it by setting its "secrets": host, port, user, and password (note that the secrets used are specific to the DB connector). You do this by creating a ConnectionConfig Secrets object by calling the [Set a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put) operation. You can set the object's attributes separately, or supply a single `url` string that encodes them all.

If you set the `verify` query parameter to `true`, the operation  will  test the connection by issuing a trivial request to the database. The `test_status` response property announces the success of the connection attempt as `succeeded` or `failed`. If the attempt has failed, the `failure_reason` property gives further details about the failure.

To skip the connection test, set `verify` to `false`.

Note: fidesops encrypts all ConnectionConfig secrets values before they're stored.

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

### Amazon Redshift

This Amazon Redshift example sets the database secrets as a `url` property and a `db_schema` property.  Redshift
databases have one or more schemas, with the default being named `public`.  If you need to set a different schema,
specify `db_schema` for Redshift, and it will be set as the `search_path` when querying.


```json title="<code>PUT api/v1/connection/my_redshift_db/secret</code>" 
{
    "url": "redshift+psycopg2://username@host.amazonaws.com:5439/database",
    "db_schema": "my_test_schema"
}
```

### Google BigQuery

For Google BigQuery, there are 2 items needed for secrets: 

`dataset` - Name of your dataset. BigQuery datasets are top-level containers (within a project) that are used to organize and control access to your tables and views.

`keyfile_creds` - Credentials from your service account JSON keyfile, accessible for download from the GCP console.  

Here's an example of what this looks like:

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

### Test your connection 

You can verify that a ConnectionConfig's secrets are valid at any time by calling the [Test a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-test_connection_config_secrets_api_v1_connection__connection_key__test_get) operation:


```
GET /api/v1/connection/application-postgresql-db/test
```

Once again, the `test_status` and `failure_reason` properties describe the success or failure of the test. If the test failed,
you should adjust the ConnectionConfig Secrets properties through additional calls to [Set a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put)


#### Connection succeeded

```json
{
    "msg": "Test completed for ConnectionConfig with key: app_postgres_db.",
    "test_status": "succeeded",
    "failure_reason": null
}
```

### Connection failed

```json
{
    "msg": "Secrets updated for ConnectionConfig with key: app_mongo_db.",
    "test_status": "failed",
    "failure_reason": "Operation Failure connecting to MongoDB."
}
```

## Associate a Dataset
Once you have a working ConnectionConfig, it can be associated to an existing [dataset](datasets.md) by calling the `/dataset` endpoint, with a JSON version of your dataset as the request body:

```json title="<code>PATCH /api/v1/connection/my_connection_key/dataset</code>"
[{
    "fides_key": "example_test_dataset",
    "name": "Example Test Dataset",
    "description": "Example of a dataset containing a variety of related tables like customers, products, addresses, etc.",
    "collections": [...]
}]
```

## Filtering ConnectionConfigs

Current available filters are the `connection_type` and whether the connection is `disabled`.

### Connection type filter

Including multiple `connection_type` query params and values will result in a query that looks for 
*any* connections with that type.

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

The `disabled` filter can show which datastores are skipped as part of privacy request execution.

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

### Testing_Status filter
The `testing_status` filter queries on the status of the last successful test:

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
The `system_status` filter surfaces either `database` or `saas`-type connectors:

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


## Search a ConnectionConfig

You can search the `name`, `key`, and `description` fields of your ConnectionConfigs with the `search` query parameter.

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

## How do ConnectionConfigs differ from Datasets?

A Dataset is an annotation of your database schema; it describes the PII category (or Data Categories) for each field that the database contains. A ConnectionConfig holds the secrets to connect to the database. Each Dataset has a foreign key to a ConnectionConfig.

After fidesops connects to your database, it generates valid queries by consulting the annotations in the Dataset.

Here is an example of how a "person" table in your PostgreSQL database might map to a fidesops
Dataset:

```yaml
Person:
  id: str
  name: str
  email: str

dataset:
  - fides_key: my_app
    name: App Dataset
    description: ...
    collections:
      - name: person
        fields:
          - name: name
            data_categories: [user.provided.identifiable.contact.name]
          - name: email
            data_categories: [user.provided.identifiable.contact.email]
          - name: id
            data_categories: [system.operations] 
```


See [Configuring Datasets](datasets.md) for more information.