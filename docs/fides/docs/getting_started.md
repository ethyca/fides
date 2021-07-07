# Getting Started

---

This section contains Quick Start guides to help you get up and running with Fides. Before starting either guide you'll need to pull the [Fides repo](https://github.com/ethyca/fides).

## Running Fides in Docker

The easiest way to get started with Fides is to launch it using the supplied `make` commands.

### Docker Requirements

1. Install Make
1. Install Docker

### Docker Setup

1. `make cli` -> this will build the required images, spin up the database, and open a shell inside of a container with `fidesctl` installed
1. About 15 seconds after the `fidesctl` shell initializes, run the `fidesctl ping` command to verify that `fidesctl` can communicate with the server.
1. `fidesctl` -> this command will list all of the possible `fidesctl` commands

## Running Fides Locally

Fides can also be spun up locally without relying on Docker or Make, however there are significantly more prerequisites.

### Local Requirements

1. Python 3.8
1. pip Version 21 or later
1. Java 8
1. sbt Version 2.12
1. MySQL DB Version 8

### Local Setup

1. Spin up the MySQL database with your desired credentials
1. `cd fides-server/`
1. Update the `application.conf` in `src/main/resources/` with the database credentials
1. `sbt flywayMigrate`
1. `sbt ~jetty:start` -> You now have a Fides Server instance up and running powered by MySQL!
1. In a new shell -> `pip install fidesctl`
1. You can now run `fidesctl ping` to verify that your installation is set up properly

## Next Steps

See the [Tutorial](tutorial.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
