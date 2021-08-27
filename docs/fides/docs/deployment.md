# Deployment

The easiest way to deploy Fides is with `Docker` and the included docker-compose file within the repo. There are separate containers for `Fidesctl`, the `API` and the `DB`.

## Requirements

1. Install MySQL 8
1. Install Python 3.8 or newer (including pip)
1. Install Docker

## Application Configuration

1. Configuration of FidesAPI will be done via environment variables passed into the container at runtime. These will need to be the same credentials that are used with your database as described in the `Setup` section.
1. Configuration of Fidesctl will be done via an `ini` file that will then be mounted onto the docker container. Fidesctl will automatically look for a file called `fides.ini` in the local directory, or at a location set by the `FIDES_CONFIG_PATH` environment variable. An example configuration file is as follows:

```ini
[user]
user_id = 1
api_key = test_api_key

[cli]
server_url = http://fidesapi:8080
```

## Setup

The setup is all done via Docker, with configuration values injected at runtime into the container.

1. Spin up a MySQL DB with the following env vars:

    ```env
    MYSQL_ROOT_PASSWORD="<root_password>"
    MYSQL_USER="<user>"
    MYSQL_PASSWORD="<user_password>"
    MYSQL_DATABASE="<db>"
    ```

1. Start the FidesAPI -> `docker run -p "127.0.0.1:8080:8080/tcp" --env FIDES_DB_JDBC_URL="jdbc:mysql://<server_address>:3306/<db>" --env FIDES_DB_JDBC_USER="<user>" --env FIDES_DB_JDBC_PASSWORD="<user_password>" ethyca/fidesapi:latest /bin/bash -c "sbt flywayMigrate && sbt ~jetty:start"`
1. Install Fidesctl -> `pip install fidesctl`
1. Write your `fides.ini` file and set your `FIDES_CONFIG_PATH` environment variable as needed
1. Run `fidesctl` to see a list of possible commands!
