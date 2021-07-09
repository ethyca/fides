# Running Fides in Docker

---

The easiest way to get started with Fides is to launch it using the supplied `make` commands, which in turn call Docker to do the heavy lifting.

## Requirements

1. Install Make
1. Install Docker
1. Clone the [Fides repo](https://github.com/ethyca/fides)

## Docker Setup

The following commands should all be run from the top-level Fides directory (where the Makefile is)

1. `make cli` -> this will build the required images, spin up the database, and open a shell inside of a container with `fidesctl` installed
1. About 15 seconds after the `fidesctl` shell initializes, run the `fidesctl ping` command to verify that `fidesctl` can communicate with the server. If it fails, wait a bit longer and try again until you get a successful response.
1. `fidesctl` -> this command will list all of the possible `fidesctl` commands

## Next Steps

See the [Tutorial](../tutorial.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
