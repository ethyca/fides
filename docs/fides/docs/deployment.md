# Production Deployment

For production deployments of Fidesctl, we suggest deploying everything individually as opposed to using the included docker-compose file. While docker-compose is great for development and experimentation, it isn't suited to production use. The following guide will walk you through setting up each component of Fidesctl as a production-grade deployment.

## Requirements

1. Install Postgres 12
1. Install Python 3.8 or newer (including pip)
1. Install Fidesctl via pip -> `pip install fidesctl`

## Setup

### Step 1: Database

Spin up a Postgresql DB and configure a user, password and database for Fidesctl to use. For example:

```env
POSTGRES_USER="fidesctl_db"
POSTGRES_PASSWORD="f1d3sctl_dB"
POSTGRES_DATABASE="fidesctl_db"
```

### Step 2: Create a Config

The next step is to create a `fidesctl.toml` config file. This is used to pass important variables to the Fidesctl applications for connections to the database, api, etc. Make sure that the username, password and database in the `database_url` connection string match what you used to configure your database.

Fidesctl will automatically look for the `fidesctl.toml` file in the current directory, in the user directory, or at the path specified by an optional `FIDESCTL_CONFIG_PATH` environment variable.

Additionally, any variable can be overriden by using a properly formatted environment variable. For instance to overwrite the `database_url` configuration value, you would set the `FIDESCTL__API__DATABASE_URL` environment variable.

The following is an example `fidesctl.toml`:

```toml
[cli]
server_url = "http://localhost:8080"

[api]
database_url = "postgresql+psycopg2://fidesctl_db:fidesdb@localhost:5432/fidesctl_db"
```

### Step 3: Fidesctl API

Next we need to prepare the database to be used by the API. Run the initial database setup via the fidesctl CLI:

```bash
fidesctl init-db
```

Now open a new terminal to run the API, as it will run there indefinitely:

`fidesctl webserver`

The webserver should now be available at `localhost:8080`, and docs are available at `localhost:8080/docs`, however the API docs can be safely ignored, as the Fidesctl CLI will abstract the API layer.

### Step 4: Fidesctl CLI

The last step is to check that everything is working! Open a new terminal window and run the following:

`fidesctl ping`

If everything is configured correctly, it will let you know that the command was successful! You've now successfully completed a complete Fidesctl deployment.
