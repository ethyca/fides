# How-To: Connect to SQL and NoSQL Databases

In this section we'll cover:

- What is a connection configuration in fidesops?
- What are the supported databases in fidesops?
- How do you set up a connection from fidesops to your databases?
- How do you update the secrets to connect to your database?


Take me directly to [api docs](http://0.0.0.0:8080/docs#/Connections) 


## What is a connection?
A connection helps you link your on-premise and remote databases to `fidesops` to eventually gather and update selected PII 
categories.  We store the details to make that connection in a `ConnectionConfig` object.

## Supported databases

Our list is growing but currently we support:

- PostgreSQL
- MongoDB


## Configuring a connection 

You'll first issue a request to create a `ConnectionConfig` object, which stores basic connection information. In 
a separate request, you'll supply and test the connection secrets (like your database's host, port, password, etc.)

### Creating a connection configuration 

Issue a PUT request to [/api/v1/connection](http://0.0.0.0:8080/docs#/Connections/put_connections_api_v1_connection_put) to create or update your `ConnectionConfigs`.

#### Sample request for a PostgreSQL database:

`PUT api/v1/connection`

```json 
[
    { 
        "name": "Application PostgreSQL DB",
        "key": "app-postgres-db",
        "connection_type": "postgres",
        "access": "read"
    }
]
```

#### Sample request for a Mongo database:

`PUT api/v1/connection`

```json 
[
    { 
        "name": "My Mongo DB",
        "key": "app-mongo-db",
        "connection_type": "mongodb",
        "access": "write"
    }
]
``` 
#### Note:
  - `name` should be a human-readable name for your database.
  - Give your database connection a unique dasherized identity `key`. If no key is supplied, we'll dasherize the `name`.
  - Specify your database type under `connection_type`.
  - `access` is the broad permissions you're granting to this connection, one of "read" or "write". If "read", we promise
to not modify your data. TODO this logic hasn't yet been added.

### Manage Connection Secrets

Issue a separate PUT request to the connection secrets endpoint to add encrypted secrets to the connection configuration
and then test that the secrets are correct.

See [`PUT /api/v1/connection/<connection_key>/secret` documentation](http://0.0.0.0:8080/docs#/Connections/put_connection_config_secrets_api_v1_connection__connection_key__secret_put)


#### Note:
This endpoint first encrypts your database secrets and saves them. Next, we build a URI from the supplied components. 
We use that URI to connect to your database and make a trivial query.  You will get a response indicating 
if the connection succeeded or failed.  You can optionally supply the entire `url` directly, and we'll use that to connect instead.

If you just want to save the secrets for now, and bypass attempting to connect, specify a `?verify=false` query param.


#### Sample request to add PostgreSQL secrets:

`PUT /api/v1/connection/app-postgres-db/secret`

```json
    {
       "host": "host.docker.internal",
       "port": 5432,
       "dbname": "postgres_example",
       "username": "postgres",
       "password": "postgres"
    }
```

#### Sample request to specify the MongoDB URL directly and bypass verification:

`PUT api/v1/connection/app-mongo-db/secret?verify=False`
```json 
{
    "url": "mongodb://mongo_user:mongo_pass@mongodb_example/mongo_test"
}
```

### Testing your connection 

If at any time, you want to verify that your connection secrets are valid, simply issue a GET request 
to the connection test endpoint.

`GET /api/v1/connection/<connection_key>/test`


#### Sample request to test your PostgreSQL database secrets 

`GET /api/v1/connection/app-postgres-db/test`

As long as we are able to test your connection, we'll return a 200 OK, but the
result of that test will be visible under `test_status".  If the test failed,
a high-level `failure_reason` will be displayed.  Make additional PUT requests
to the connection secrets endpoints to edit your connection components and try again.

```json
{
    "msg": "Test completed for ConnectionConfig with key: app-postgres-db.",
    "test_status": "succeeded",
    "failure_reason": null
}
```
OR

```json
{
    "msg": "Secrets updated for ConnectionConfig with key: app-mongo-db.",
    "test_status": "failed",
    "failure_reason": "Operation Failure connecting to MongoDB."
}


```


## How do connections differ from datasets?

A *Dataset* is the annotation of your database schema, while the *ConnectionConfig* holds the secrets to connect 
to that database.  A Dataset has a foreign key to a ConnectionConfig. 

After we connect to your database, we use the annotations stored in your dataset to know which fields are of 
which type and which data categories so we can generate queries against your database.

Here is an example of how a "person" table in your PostgreSQL database might map to a fides-annotated
dataset:

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
