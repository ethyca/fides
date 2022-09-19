# Installation from Docker

The `fides` image is published on the [ethyca/fidesctl DockerHub](https://hub.docker.com/r/ethyca/fides/tags) and maintained by the Fides team. To decide if a Docker installation is right for your use case, see the [installation overview](./overview.md).

These reference images contain all of the extras and dependencies for running the Python application, but do not contain the required Postgres database.

## System requirements

See the the [Prerequisites and Dependencies](../installation/prerequisites.md#docker-requirements) page for the minimum Docker requirements.

## Docker configuration

Within your project's root folder, create a file named `docker-compose.yml`. The following example will create the sample databases, and spin up the Fides webserver and UI.

```yaml title="docker-compose.yml"
services:
  fides:
    image: ethyca/fides:local
    command: uvicorn --host 0.0.0.0 --port 8080 --reload fides.api.main:app
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://0.0.0.0:8080/health" ]
      interval: 20s
      timeout: 5s
      retries: 5
    ports:
      - "8080:8080"
    depends_on:
      fides-db:
        condition: service_healthy
      worker:
        condition: service_started
    expose:
      - 8080
    environment:
      FIDES__CONFIG_PATH: "/fides/.fides/fides.toml"
      FIDES__CLI__ANALYTICS_ID: ${FIDES__CLI__ANALYTICS_ID}
      FIDES__CLI__SERVER_HOST: "fides"
      FIDES__CLI__SERVER_PORT: "8080"
      FIDES__DATABASE__SERVER: "fides-db"
      FIDES__DEV_MODE: "True"
      FIDES__EXECUTION__WORKER_ENABLED: "True"
      FIDES_TEST_MODE: "True"
      FIDES__USER__ANALYTICS_OPT_OUT: "True"
    volumes:
      - type: bind
        source: .
        target: /fides
        read_only: False

  fides-ui:
    image: ethyca/fides:local-ui
    command: npm run dev-docker
    depends_on:
      - fides
    expose:
      - 3000
    ports:
      - "3000:3000"
    volumes:
      - type: bind
        source: .
        target: /fides
        read_only: False
    environment:
      - NEXT_PUBLIC_FIDESCTL_API_SERVER=http://fides:8080

  fides-db:
    image: postgres:12
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U postgres" ]
      interval: 15s
      timeout: 5s
      retries: 5
    volumes:
      - postgres:/var/lib/postgresql/data
    expose:
      - 5432
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: "postgres"
      POSTGRES_PASSWORD: "fides"
      POSTGRES_DB: "fides"
    deploy:
      placement:
        constraints:
          - node.labels.fides.app-db-data == true

  redis:
    image: "redis:6.2.5-alpine"
    command: redis-server --requirepass testpassword
    environment:
      - REDIS_PASSWORD=testpassword
    expose:
      - 6379
    ports:
      - "0.0.0.0:6379:6379"

  worker:
    image: ethyca/fides:local
    command: fides worker
    depends_on:
      redis:
        condition: service_started
    restart: always
    volumes:
      - type: bind
        source: ./
        target: /fides
        read_only: False
      - /fides/src/fides.egg-info

volumes:
  postgres: null

```

## Run your container

If using the above example file, ensure nothing is running on port `5432`, `3000`, or `8080` before using the following commands:

1. `docker-compose up -d` will start your docker-compose file in the background.
1. `docker-compose run --rm fides /bin/bash` opens a shell within the Fides container.

### Initialize Fides 

Initializing the project will create a configuration file with default values, and generate a directory to house your Fides resources.

```sh title="Initialize Fides"
fides init
```

```txt title="Expected Output"
Initializing Fides...
----------
Created a './.fides' directory.
----------
Created a fides config file: ./.fides/fides.toml
To learn more about configuring fides, see:
    https://ethyca.github.io/fides/installation/configuration/
----------
For example policies and help getting started, see:
    https://ethyca.github.io/fides/guides/policies/
----------
Fides initialization complete.
```

### Verify your installation status

Running `fidesctl status` confirms that your `fides` CLI can reach the server.

Once your installation is running, you can use `fides` from the shell to get a list of all the possible [CLI commands](../cli.md).
