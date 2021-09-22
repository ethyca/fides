# Deployment

For production deployments of Fidesctl, we suggest deploying everything individually as opposed to using the included docker-compose file. While docker-compose is great for development and experimentation, it isn't suited to production use. The following guide will walk you through setting up each component of Fidesctl as a production-grade deployment.

## Requirements

1. Install Postgres 12
1. Install Python 3.8 or newer (including pip)
1. Install Fidesctl via pip -> `pip install fidesctl`

## Setup

### Step 1: Database

1. Spin up a Postgresql DB with the following env vars:

    ```env
    POSTGRES_USER="<user>"
    POSTGRES_PASSWORD="<password>"
    POSTGRES_DATABASE="fidesdb"
    ```

1. Next, run the initial database setup via the fidesctl CLI:

    ```bash
    fidesctl initdb
    ```

### Step 2: Create a Config

The next step is to create a `fides.toml` config file. This is used to pass important variables to the Fidesctl applications for connections to the database, api, etc.

The following is an example `fides.toml`:

```toml
[user]
user_id = "1"
api_key = "test_api_key"

[cli]
server_url = "http://fidesctl:8080"

[api]
database_url = "postgresql+psycopg2://fidesdb:fidesdb@fidesdb:5432/fidesdb"
```

### Step 2: Fidesctl API

The next step is to spin up the Fidesctl API. Make sure to do this in a separate terminal/process as it will run there indefinitely:

`fidesctl webserver`

The webserver should now be available at `localhost:8080`, and docs are available at `localhost:8080/docs`, however the API docs can for the most part safely be ignored, as the Fidesctl CLI will abstract away the API layer.

### Step 3: Fidesctl CLI
