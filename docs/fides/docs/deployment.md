# Deployment

The easiest way to deploy Fides is with `Docker` and the included docker-compose file within the repo. There are separate containers for `Fidesctl`, the `API` and the `DB`.

## Requirements

1. Install Make
1. Install Docker (Docker compose is bundled with Docker in current versions)
1. Clone the [Fides repo](https://github.com/ethyca/fides)

## Application Configuration

1. Configuration of FidesAPI will be done via environment variables passed into the container at runtime. These will need to be the same credentials that are used with your database:
    * `FIDES_DB_JDBC_URL="jdbc:mysql://fides-db:3306/fidesdb"`
    * `FIDES_DB_JDBC_USER="fidesdb"`
    * `FIDES_DB_JDBC_PASSWORD="fidesdb"`

1. Configuration of Fidesctl will be done via a `.ini` file that will then be mounted onto the docker container. Fidesctl will automatically look for files called `fides.ini` in the root and home directories, so that's what it should be called and where it should be mounted. An example configuration file is as follows:

```ini
[user]
user_id = 1
api_key = test_api_key

[cli]
server_url = http://fidesapi:8080
```

## Setup

1. Spin up a MySQL 8 instance and make sure that it will be accessible from wherever your FidesAPI container is going to run
1. Run FidesAPI using the following command: `docker run ethyca/fidesapi:latest /bin/bash -c "sbt flywayMigrate && sbt ~jetty:start"`
1. Run Fidesctl using the following command: `docker run ethyca/fidesctl:latest -v ./fides.ini:/fides.ini /bin/bash -c "sleep infinity"`
1. Connect to the container Fidesctl container to run commands
