# Deployment

We recommend deploying Fides with `Docker` using the included docker-compose file [found here in the repo](https://github.com/ethyca/fides/blob/main/docker-compose.yml). There are separate containers for `Fidesctl`, the `API` and the `DB`.

## Requirements

1. Install Postgres 12
1. Install Python 3.8 or newer (including pip)

## Setup

The setup is done via Docker, with configuration values injected at runtime into the container.

1. Spin up a MySQL DB with the following env vars:

    ```env
    MYSQL_ROOT_PASSWORD="<root_password>"
    MYSQL_USER="<user>"
    MYSQL_PASSWORD="<user_password>"
    MYSQL_DATABASE="<db>"
    ```

1. Start the FidesAPI -> `docker run -p "127.0.0.1:8080:8080/tcp" --env FIDES_DB_JDBC_URL="jdbc:mysql://<server_address>:3306/<db>" --env FIDES_DB_JDBC_USER="<user>" --env FIDES_DB_JDBC_PASSWORD="<user_password>" ethyca/fidesapi:latest /bin/bash -c "sbt flywayMigrate && sbt ~jetty:start"`
1. Install Fidesctl -> `pip install fidesctl`
1. Configuration of Fidesctl will be done via an `ini` file that will then be mounted onto the docker container. Fidesctl will automatically look for a file called `fides.ini` in the local directory, or at a location set by the `FIDES_CONFIG_PATH` environment variable. 
    <details>
        <summary>Here's an example ini file to get you started</summary>
        
    ```ini
    [user]
    user_id = 1
    api_key = test_api_key

    [cli]
    server_url = http://fidesapi:8080
    ```
    </details>

    Write your `fides.ini` file and set your `FIDES_CONFIG_PATH` environment variable as needed

5. Run `fidesctl` to see a list of possible commands!
