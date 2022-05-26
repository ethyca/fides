# How-To: Connect to SQL and NoSQL Databases

In this section we'll cover:

- What's a "connection"?
- Which databases does Fidesops support?
- How do you create a ConnectionConfig object?
- How do you identify the database that a ConnectionConfig connects to?
- How do you test and update a ConnectionConfig's Secrets?
- How does a ConnectionConfig differ from a Dataset?


Take me directly to the [ConnectionConfig API documentation](/fidesops/api#operations-tag-Connections).

## What is a connection?

A _connection_ links your databases to Fidesops, so you can gather and update selected PII 
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

## Creating a ConnectionConfig object 

The connection between Fidesops and your database is represented by a _ConnectionConfig_ object. To create a ConnectionConfig, you issue a request to the [Create a ConnectionConfig](/fidesops/api/#operations-Connections-put_connections_api_v1_connection_put) operation, passing a payload that contains the properties listed below. 

* `name`  is a human-readable name for your database.

* `key`  is a string token that uniquely identifies your ConnectionConfig object. If you don't supply a `key`, the `name` value, converted to snake-case, is used. For example, if the `name` is `Application PostgreSQL DB`, the converted key is `application_postgresql_db`.

* `connection-type` specifies the type of database. Valid values are `postgres`, `mongodb`, `mysql`, `mariadb`, `mssql`, `redshift`, `snowflake`, and `bigquery`.

* `access` sets the connection's permissions, one of "read" (Fidesops may only read from your database) or "write" (Fidesops can read from and write to your database).

While the ConnectionConfig object contains meta information about the database, you'll notice that it doesn't actually identify the database itself. We'll get to that when we set the ConnectionConfig's "secrets".


#### Example 1: PostgreSQL ConnectionConfig

``` 
PATCH api/v1/connection

[
  { 
    "name": "Application PostgreSQL DB",
    "key": "application_postgresql_db",
    "connection_type": "postgres",
    "access": "read"
  }
]
```

#### Example 2: MongoDB ConnectionConfig



```
PATCH api/v1/connection

[
  { 
    "name": "My Mongo DB",
    "key": "my_mongo_db",
    "connection_type": "mongodb",
    "access": "write"
  }
]
``` 

#### Example 3: MySQL ConnectionConfig 

```
PATCH api/v1/connection 
[
  { 
    "name": "My MySQL DB",
    "key": "my_mysql_db",
    "connection_type": "mysql",
    "access": "write"
  }
]
``` 

#### Example 4: MariaDB ConnectionConfig

```
PATCH api/v1/connection 
[
  { 
    "name": "My Maria DB",
    "key": "my_maria_db",
    "connection_type": "mariadb",
    "access": "write"
  }
]
``` 

#### Example 5: MsSQL ConnectionConfig

```
PATCH api/v1/connection 
[
  { 
    "name": "My MsSQL DB",
    "key": "my_mssql_db",
    "connection_type": "mssql",
    "access": "write"
  }
]
``` 

#### Example 6: Manual ConnectionConfig

```
PATCH api/v1/connection 
[
  {
    "name": "Manual connector",
    "key": "manual_connector",
    "connection_type": "manual",
    "access": "read"
  }
]
``` 

### Set the ConnectionConfig's Secrets

After you create a ConnectionConfig, you explain how to connect to it by setting its "secrets": host, port, user, and password (note that the secrets used are specific to the DB connector). You do this by creating a ConnectionConfig Secrets object by calling the [Set a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put) operation. You can set the object's attributes separately, or supply a single `url` string that encodes them all.

If you set the `verify` query parameter to `true`, the operation  will  test the connection by issuing a trivial request to the database. The `test_status` response property announces the success of the connection attempt as `succeeded` or `failed`. If the attempt has failed, the `failure_reason` property gives further details about the failure.

To skip the connection test, set `verify` to `false`.

Note: Fidesops encrypts all ConnectionConfig Secrets values before they're stored.


#### Example 1: Set the secrets separately

This example sets the database secrets through separate properties and then tests the connection.

```
PUT /api/v1/connection/application-postgresql-db/secret?verify=true`

{
   "host": "host.docker.internal",
   "port": 5432,
   "dbname": "postgres_example",
   "username": "postgres",
   "password": "postgres"
}
```

#### Example 2: Set the secrets as a URL

This example sets the database secrets as a single `url` property, and skips the connection test.


```
PUT api/v1/connection/my_mongo_db/secret?verify=false`
 
{
    "url": "mongodb://mongo_user:mongo_pass@mongodb_example/mongo_test"
}
```

#### Example 3: Amazon Redshift: Set URL and Schema

This Amazon Redshift example sets the database secrets as a `url` property and a `db_schema` property.  Redshift
databases have one or more schemas, with the default being named `public`.  If you need to set a different schema,
specify `db_schema` for Redshift, and it will be set as the `search_path` when querying.


```
PUT api/v1/connection/my_redshift_db/secret`
 
{
    "url": "redshift+psycopg2://username@host.amazonaws.com:5439/database",
    "db_schema": "my_test_schema"
}
```

#### Example 4: Google BigQuery

For Google BigQuery, there are 2 items needed for secrets: 

`dataset` - Name of your dataset. BigQuery datasets are top-level containers (within a project) that are used to organize and control access to your tables and views.

`keyfile_creds` - Credentials from your service account JSON keyfile, accessible for download from the GCP console.  

Here's an example of what this looks like:

```
PUT api/v1/connection/my_bigquery_db/secret`

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

### Testing your connection 

You can verify that a ConnectionConfig's secrets are valid at any time by calling the [Test a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-test_connection_config_secrets_api_v1_connection__connection_key__test_get) operation:


```
GET /api/v1/connection/application-postgresql-db/test
```

Once again, the `test_status` and `failure_reason` properties describe the success or failure of the test. If the test failed,
you should adjust the ConnectionConfig Secrets properties through additional calls to [Set a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put)


#### Example 1: Connection Succeeded

```json
{
    "msg": "Test completed for ConnectionConfig with key: app_postgres_db.",
    "test_status": "succeeded",
    "failure_reason": null
}
```

#### Example 2: Connection Failed

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

## How do ConnectionConfigs differ from Datasets?

A Dataset is an annotation of your database schema; it describes the PII category (or Data Categories) for each field that the database contains. A ConnectionConfig holds the secrets to connect to the database. Each Dataset has a foreign key to a ConnectionConfig.

After Fidesops connects to your database, it generates valid queries by consulting the annotations in the Dataset.

Here is an example of how a "person" table in your PostgreSQL database might map to a Fidesops
Dataset:

```
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


See [How-To: Configure Datasets](datasets.md) for more information.