# Running Fides in Docker

---

The recommended way to get Fides running is to launch it using the supplied `make` commands that will spin up the entire project via `docker-compose`. 

## Requirements

1. Install Make
1. Install Docker (Docker compose is bundled with Docker in current versions)
1. Clone the [Fides repo](https://github.com/ethyca/fides)

## Docker Setup

The following commands should all be run from the top-level Fides directory (where the Makefile is)

1. `make compose-build` -> This will build all of the required images
1. `make init-db` -> Spins up the database and runs the initialization scripts
1. `make cli` -> This will spin up the entire project and open a shell within the Fidesctl container, with the FidesAPI being accessible. This command will "hang" for a bit, as Fidesctl will wait for the FidesAPI service to be healthy before spinning up the terminal.
1. `fidesctl` -> this command will list all of the possible `fidesctl` commands! You're now ready to start using with Fides.

## Next Steps

See the [Tutorial](../tutorial.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
