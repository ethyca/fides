# Deployment Guide

!!! Tip "This guide is intended for production deployments. To quickly experiment with Fides, clone the [source repository](https://github.com/ethyca/fides), and use the built-in docker compose configuration to run a demo environment."

A production-ready instance of Fides can be deployed leveraging the cloud infrastructure your organization is most familiar with.

Fully deployed, Fides consists of the following individual systems:

1. [**Hosted Database**](#step-1-setup-hosted-database): A PostgreSQL database server used for permanent storage of configuration data for the webserver.
2. [**Hosted Cache**](#step-2-setup-hosted-cache): A Redis database server used as a temporary cache during execution and task scheduling.
3. [**Fides Weberver**](#step-3-setup-fidesops-web-server): The main application, which houses the Admin UI and API endpoints.

Optionally, the Fides [Privacy Center](#step-4-setup-privacy-center-\(optional\)) can be deployed as a pre-built way to receive privacy requests.

## Set up the hosted database

Fides uses an application database for persistent storage. Any hosted PostgreSQL database that meets the current [project requirements](./installation/prerequisites.md) is acceptable, as long as it's accessible. 

Options include:

* A managed PostgreSQL database services (e.g., AWS RDS, GCP Cloud SQL, Azure Database)
* A self-hosted PostgreSQL Docker container with a persistent volume mount (e.g., a Kubernetes cluster)
* A self-hosted PostgreSQL server (e.g., an EC2 server)

!!! Tip "As long as your database will be accessible by your Fides webserver, there is no need to expose it to the public Internet."

### Configure your database
Follow the documentation for the option of your choice to configure a production-grade PostgreSQL database.

Once your database is up and running, create a **unique user** and **database** for Fides to use, and assign your Fides user a secure password.  

### Update your Fides configuration
Use your database information to set the following values in your Fides [configuration](./installation/configuration.md). The options for the `[postgres]` section of the `fides.toml` file are outlined below, but may be substituted with environment variables.

| Name | Default | Description |
| :---- | :------- | :----------- |
| `user` | `postgres` | The database user Fides will use to log in to the application database. |
| `password`| `fides` | The password for the Fides user. |
| `server` | `fides-db` | The hostname of the Postgres database server. |
| `port` | `5432` | The port at which the Postgres database will be accessible. |
| `db` | `fides` | The name of the Postgres database. |

## Set up the hosted cache

During privacy request execution, Fides collects result data in a temporary Redis cache that automatically expires to ensure personal data is never retained erroneously. Any hosted Redis database that meets the current [project requirements](./installation/prerequisites.md) is acceptable, from a Docker [Redis](https://hub.docker.com/_/redis) container to a managed service (e.g., AWS ElastiCache, GCP Memorystore, Azure Cache, Redis Cloud).

!!! Tip "As long as your cache will be accessible by your Fides webserver, there is no need to expose it to the public Internet."

### Configure your cache
Follow the documentation for the option of your choice to configure a production-grade Redis cache.

Once your cache is available, ensure you enable a password (via Redis [`AUTH`](https://redis.io/commands/auth)) to provide additional security, and keep track of your connection credentials.

### Update your Fides configuration
Use your database information to set the following values in your Fides [configuration](./installation/configuration.md). The options for the `[redis]` section of the `fides.toml` file are outlined below, but may be substituted with environment variables.

| Config Variable | Example | Description |
| :--- | :--- | :--- | 
| `host` | N/A | The network address for the application Redis cache. |
| `port` | `6379` | The port at which the application cache will be accessible. |
| `user`  | N/A | The user with which to login to the Redis cache. |
| `password` | N/A | The password with which to login to the Redis cache. |
| `db_index` | N/A | The application will use this index in the Redis cache to cache data. |

## Set up the webserver

The Fides webserver is a [FastAPI](https://fastapi.tiangolo.com/) application with a [Uvicorn](https://www.uvicorn.org/) server to handle requests. The host requirements for the webserver are minimal:

* A general purpose webserver (e.g. for AWS EC2, a `t2.small` or larger)
* Docker version 20.10.8 or newer (if installing via Docker)
* OR Python 3.8 or newer (if installing via Python)
* No persistent storage requirements (this is handled by the hosted database)

### Using docker

Ensure that Docker is running on your host, and satisfies the [minimum requirements](./installation/requirements.md).

#### Pull the docker image
Run the following command to pull the latest image from Ethyca's [DockerHub](https://hub.docker.com/r/ethyca/fidesops):

```
docker pull ethyca/fidesops
``` 

#### Configure Fides
A number of environment variables are required for a minimum working [configuration](./installation/configuration.md). You can provide a configuration by creating an `.env` file and passing it in via the [`--env-file {file}` option](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file), by providing individual variables with the `--env {VAR}` option, or directly to your docker host.

At a minimum, you'll need to configure the following:

| Config Variable | Example | Description |
|---|---|---|
| `FIDES__SECURITY__APP_ENCRYPTION_KEY` | athirtytwocharacterencryptionkey | An AES256 encryption key used for DB & JWE encryption. Must be exactly 32 characters (256bits). |
| `FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID` | fidesadmin | client ID used for the "root" OAuth client |
| `FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET` | fidesadminsecret | client secret used for the "root" OAuth client |
| `FIDES__DATABASE__SERVER` | postgres.internal | hostname for your database server |
| `FIDES__DATABASE__PORT` | 5432 |port for your database server |
| `FIDES__DATABASE__USER` | fidesops | username `fidesops` should use to access the database |
| `FIDES__DATABASE__PASSWORD` | fidessecret | password `fidesops` should use to access the database |
| `FIDES__DATABASE__DB` | fides | database name |
| `FIDES__REDIS__HOST` | redis.internal | hostname for your Redis server |
| `FIDES__REDIS__PORT` | 6379 | port for your Redis server |
| `FIDES__REDIS__PASSWORD` | fidessecret | password `fidesops` should use to access Redis |


#### Start your server

Once pulled, you can start your server with:

```
docker run ethyca/fidesops -p 8080:8080
```

To include your environment variables, you can run the following: 
```sh
docker run \
  -p 8080:8080 \
  --env FIDES__SECURITY__APP_ENCRYPTION_KEY="athirtytwocharacterencryptionkey" \
  --env FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID="fidesadmin" \
  --env FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET="fidesadminsecret" \
  --env FIDES__DATABASE__SERVER="postgres.internal" \
  --env FIDES__DATABASE__PORT="5432" \
  --env FIDES__DATABASE__USER="fides" \
  --env FIDES__DATABASE__PASSWORD="fidessecret" \
  --env FIDES__DATABASE__DB="fides" \
  --env FIDES__REDIS__HOST="redis.internal" \
  --env FIDES__REDIS__PORT=6379 \
  --env FIDES__REDIS__PASSWORD="fidessecret" \
  ethyca/fidesops
```

If you prefer to create your .env file and pass an `--env-file` variable: 
```
docker run \
  -p 8080:8080 \
  --env-file=<ENV FILE NAME>.env \
  ethyca/fidesops
```

```env title="<code>config.env</code>"
FIDES__SECURITY__APP_ENCRYPTION_KEY="athirtytwocharacterencryptionkey" 
FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID="fidesadmin" 
FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET="fidesadminsecret" 
FIDES__DATABASE__SERVER="postgres.internal" 
FIDES__DATABASE__PORT="5432" 
FIDES__DATABASE__USER="fides" 
FIDES__DATABASE__PASSWORD="fidessecret" 
FIDES__DATABASE__DB="fides" 
FIDES__REDIS__HOST="redis.internal" 
FIDES__REDIS__PORT=6379 
FIDES__REDIS__PASSWORD="fidessecret"
```

Note that there's no need for a persistent volume mount. The webserver is fully ephemeral, and relies on the database for its permanent state.

### Using Python

Follow the [PyPI installation guide](./installation/pypi.md) for initializing and configuring Fides on your host.

### Test the webserver

To test that your server is running, visit `http://{server_url}/health` in your browser (e.g. http://0.0.0.0:8080/health) and you should see `{"webserver": "healthy", "database": "healthy", "cache": "healthy"}`. 

You can also visit the hosted UI at `http://{server_url}/`.

## Set up the Privacy Center (Optional)

Ensure that Docker is running on your host, and satisfies the [minimum requirements](./installation/requirements.md).

Run the following command to pull the latest image from Ethyca's [DockerHub](https://hub.docker.com/r/ethyca/fides):

```
docker pull ethyca/fides-privacy-center
``` 

More information about configuration options can be found [here](https://ethyca.github.io/fidesops/ui/privacy_center/).

Once pulled and configured, you can run the following within your project to start the server: 

```sh
docker run --rm \
  -v $(pwd)/config:/app/config \
  -p 3000:3000 ethyca/fides-privacy-center:latest
```

