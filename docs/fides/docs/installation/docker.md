# Installation from Docker

The `fides` image is published on the [ethyca/fides DockerHub](https://hub.docker.com/r/ethyca/fides/tags) and maintained by the Fides team. To decide if a Docker installation is right for your use case, see the [installation overview](./overview.md).

These reference images contain all of the extras and dependencies for running the Python application, but do not contain the required Postgres database.

!!! Tip "To quickly experiment with Fides, clone the [source repository](https://github.com/ethyca/fides), and use the built-in docker compose configuration to run a complete demo environment."

## System requirements
Ensure that Docker is running on your host prior to starting. See the the [Prerequisites and Dependencies](requirements.md#docker-requirements) page for the minimum Docker requirements.

## Pull the docker image
Run the following command to pull the latest image from Ethyca's [DockerHub](https://hub.docker.com/r/ethyca/fides):

```
docker pull ethyca/fides
``` 

## Set up your database

Configure your own Postgres database according to the configuration of your choice, ensuring it satisfies the project [requirements](./requirements.md). Enable a username and password, and keep track of your connection credentials.

## Set up your cache
Configure your own Redis cache according to the configuration of your choice, ensuring it satisfies the project [requirements](./requirements.md). Enable a password (via Redis [`AUTH`](https://redis.io/commands/auth)) to provide additional security, and keep track of your connection credentials.
## Configure Fides

Fides configuration variables are maintained in either a `fides.toml` file, or environment variables. These should be replaced with the connection credentials for your Postgres and Redis instances, as well as any other information unique to your deployment. 

See the [Configuration guide](configuration.md) for a full list of settings, and a sample `fides.toml`.

## Running the webserver
Once configured, you can start your server:

```
docker run ethyca/fides
```

With the Fides webserver running, the hosted UI is available at `http://{server_url}/` (e.g. `http://localhost:8080/`). 


