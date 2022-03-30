# Running Fidesctl in Docker

---

The recommended way to get Fidesctl running is via Docker. The following guide will describe how to get things going, step-by-step.

## System Requirements

Docker and Docker-Compose are the only requirements here.

1. Install `docker` locally (see [Docker Desktop](https://www.docker.com/products/docker-desktop) or your preferred installation). The minimum verified Docker version is `20.10.8`
1. If your `docker` installation did not include `docker-compose`, make sure to get at least version `1.29.0`. Installation instructions can be found [here](https://docs.docker.com/compose/install/).
1. In the directory from where you will run the docker compose file, create a `.fides` directory to then mount in the `fidesctl` container.

## Initializing Fidesctl

Even though we're running fidesctl in Docker, we still need to initialize fidesctl locally to then mount those files into the Docker container.

```sh title="Initialize Fidesctl"
fidesctl init
```

```txt title="Expected Output"
No config file found. Using default configuration values.
Initializing Fidesctl...

Created a '.fides' directory.

Fides needs your permission to send Ethyca a limited set of anonymous usage statistics.
Ethyca will only use this anonymous usage data to improve the product experience, and will never collect sensitive or personal data.

***
Don't believe us? Check out the open-source code here:
    https://github.com/ethyca/fideslog
***

To opt-out of all telemetry, press "n". To continue with telemetry, press any other key.

Created a config file at '.fides/fidesctl.toml'. To learn more, see:  
            https://ethyca.github.io/fides/installation/configuration/

Fidesctl initialization complete.
```

## Docker Setup

This is a reference file that you can copy/paste into a local `docker-compose.yml` file. It will create a database and spin up the fidesctl webserver. Make sure that you don't have anything else running on port `5432` or `8080` before using this file.

```docker-compose title="docker-compose.yml"
services:
  fidesctl:
    image: ethyca/fidesctl:1.2.0
    command: fidesctl webserver
    healthcheck:
      test: ["CMD", "curl", "-f", "http://0.0.0.0:8000/health"]
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
      - FIDESCTL__CLI__SERVER_URL=http://fidesctl:8080
      - FIDESCTL__API__DATABASE_URL=postgres:fidesctl@fidesctl-db:5432/fidesctl
    volumes:
      - type: bind
        source: ./.fides/ # Update this to be the path of your .fides/ folder
        target: /fides/.fides/
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

Now we can start interacting with our installation. Let's run the following commands to get going:

1. `docker-compose up -d` -> This will spin up the docker-compose file in the background.
1. `docker-compose run --rm fidesctl /bin/bash` -> This opens a shell within the fidesctl container.
   

Now that you're up and running, you can use `fidesctl` from the shell to get a list of all the possible [CLI commands](../cli.md).

## Next Steps

You're now ready to start enforcing privacy with Fidesctl!

See the [Tutorial](../tutorial/index.md) page for a step-by-step guide on setting up a Fidesctl data privacy workflow.
