# Getting Started with Fidesctl in Docker

---

The recommended way to get Fidesctl running is via Docker. The following guide will describe how to get things going, step-by-step.

## System Requirements

Docker and Docker-Compose are the only requirements here.

1. Install `docker` locally (see [Docker Desktop](https://www.docker.com/products/docker-desktop) or your preferred installation). The minimum verified Docker version is `20.10.8`
1. If your `docker` installation did not include `docker-compose`, make sure to get at least version `1.29.0`. Installation instructions can be found [here](https://docs.docker.com/compose/install/).

## Docker Setup

This is a reference file that you can copy/paste into a local `docker-compose.yml` file.

```docker-compose title="docker-compose.yml"
services:
  fidesctl:
    image: ethyca/fidesctl:1.0.0
    command: fidesctl
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
    volumes:
      - type: bind
        source: .
        target: /fides
        read_only: False
    env_file:
      - env_files/fidesctl.env

  fidesctl-db:
    image: postgres:12
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - postgres:/var/lib/postgresql/data
    expose:
      - 5432
    ports:
      - "5432:5432"
    env_file:
      - env_files/db.env

  docs:
    build:
      context: docs/fides/
      dockerfile: Dockerfile
    volumes:
      - ./docs/fides:/docs
    expose:
      - 8000
    ports:
      - "8000:8000"

volumes:
  postgres:

```

1. `fidesctl ping` -> This confirms that your `fidesctl` CLI can reach the server and everything is ready to go!

    ```bash
    root@796cfde906f1:/fides/fidesctl# fidesctl ping
    Pinging http://fidesctl:8080/health...
    {
        "data": {
            "message": "Fidesctl API service is healthy!"
        }
    }
    ```

## Next Steps

Now that you're up and running, you can use `fidesctl` from the shell to get a list of all the possible CLI commands. You're now ready to start enforcing privacy with Fidesctl!

See the [Tutorial](../tutorial/index.md) page for a step-by-step guide on setting up a Fidesctl data privacy workflow.
