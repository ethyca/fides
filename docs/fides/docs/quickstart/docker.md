# Running Fidesctl in Docker

The recommended way to get Fidesctl running is via Docker. The following guide will describe how to get things going, step-by-step.

## System Requirements

Docker and Docker-Compose are the only requirements here.

1. Install `docker` locally (see [Docker Desktop](https://www.docker.com/products/docker-desktop) or your preferred installation). The minimum verified Docker version is `20.10.8`
1. If your `docker` installation did not include `docker-compose`, make sure to get at least version `1.29.0`. Installation instructions can be found [here](https://docs.docker.com/compose/install/).
1. In a new project folder (or in the root directory of your current project), create a `.fides` folder.

## Docker Setup

This is a reference file that you can copy/paste into a local `docker-compose.yml` file, which should be created in your project's root folder. It will create a database and spin up the fidesctl webserver. 

Make sure that you don't have anything else running on port `5432` or `8080` before using this file.

```docker-compose title="docker-compose.yml"
services:
  fidesctl:
    image: ethyca/fidesctl
    command: fidesctl webserver
    healthcheck:
      test: ["CMD", "curl", "-f", "http://0.0.0.0:8000/api/v1/health"]
      interval: 5s
      timeout: 5s
      retries: 5
    depends_on:
      fidesctl-db:
        condition: service_healthy
    expose:
      - 8080
    ports:
      - "8080:8080"
    environment:
      FIDESCTL_TEST_MODE: "True"
      FIDESCTL__CLI__SERVER_HOST: "fidesctl"
      FIDESCTL__CLI__SERVER_PORT: "8080"
      FIDESCTL__API__DATABASE_HOST: "fidesctl-db"
    volumes:
      - type: bind
        source: .
        target: /fides
        read_only: False

  fidesctl-db:
    image: postgres:12
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - postgres-fidesctl:/var/lib/postgresql/data
    expose:
      - 5432
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=fidesctl
      - POSTGRES_DB=fidesctl

volumes:
  postgres-fidesctl:

```

Now you can start interacting with your installation. Run the following commands to get going:

1. `docker-compose up -d` -> This will spin up the docker-compose file in the background.
1. `docker-compose run --rm fidesctl /bin/bash` -> This opens a shell within the fidesctl container.
1. `fidesctl init` -> This will create a default configuration file at `./.fides/fidesctl.toml`.

    ```bash
    Created a fidesctl config file: ./.fides/fidesctl.toml
    To learn more about configuring fidesctl, see:
      https://ethyca.github.io/fides/installation/configuration/
    ----------
    For example policies and help getting started, see:
      https://ethyca.github.io/fides/guides/policies/
    ----------
    Fidesctl initialization complete.

    ```

1. `fidesctl status` -> This confirms that your `fidesctl` CLI can reach the server and everything is ready to go!
   

Once your installation is running, you can use `fidesctl` from the shell to get a list of all the possible [CLI commands](../cli.md).

## Next Steps

You're now ready to start enforcing privacy with Fidesctl!

See the [Tutorial](../tutorial/index.md) page for a step-by-step guide on setting up a Fidesctl data privacy workflow.
