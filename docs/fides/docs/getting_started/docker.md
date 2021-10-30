# Getting Started with Fidesctl in Docker

---

The recommended way to get Fidesctl running is to launch it using Docker and Docker-Compose. The `make` commands wrap `docker-compose` commands that will spin up each piece of the project.

## System Requirements

1. Install `make` locally (see [Make on Homebrew (Mac)](https://formulae.brew.sh/formula/make), [Make for Windows](http://gnuwin32.sourceforge.net/packages/make.htm), or your preferred installation)
1. Install `docker` locally (see [Docker Desktop](https://www.docker.com/products/docker-desktop) or your preferred installation; use a recent enough version so that `docker-compose` is also available)
1. Clone the [Fidesctl repo](https://github.com/ethyca/fides) and `cd` into the `fides` directory

## Docker Setup

The following commands should all be run from the top-level `fides` directory (where the Makefile is):

1. `make cli` -> This will spin up the entire project and open a shell within the `fidesctl` container, with the `fidesapi` being accessible. This command will "hang" for a bit, as `fidesctl` will wait for the API to be healthy before launching the shell. Once you see the `fidesctl#` prompt, you know you're ready to go:

    ```bash
    ~/git/fides% make cli
    Build the images required in the docker-compose file...
    ...
    Building fidesapi
    ...
    Building fidesctl
    ...
    Building docs
    ...
    root@1a742083cedf:/fides/fidesctl#
    ```

1. `fidesctl init-db` -> Builds the required images, spins up the database, and runs the initialization scripts:

    ```bash
    ~/git/fides% fidesctl init-db
    INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
    INFO  [alembic.runtime.migration] Will assume transactional DDL.
    ```

1. `fidesctl ping` -> This confirms that your `fidesctl` CLI can reach the server and everything is ready to go!

    ```bash
    root@796cfde906f1:/fides/fidesctl# fidesctl ping
    Pinging http://fidesapi:8080...
    Fidesctl is healthy!
    ```

## Next Steps

Now that you're up and running, you can use `fidesctl` from the shell to get a list of all the possible CLI commands. You're now ready to start enforcing privacy with Fidesctl!

See the [Tutorial](../tutorial/overview.md) page for a step-by-step guide on setting up a Fidesctl data privacy workflow.
