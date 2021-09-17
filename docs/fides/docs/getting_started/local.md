# Running Fides Locally

Fides can also be spun up locally without relying on Docker or Make, however there are significantly more prerequisites. This is __not the recommended way to run Fides!__ Please see the [Getting Started with Docker](docker.md) guide for the recommended setup experience.

## Local Requirements

1. Python 3.8
1. pip Version 21 or later
1. Java 11
1. sbt Version 2.12
1. PostgreSQL DB Version 13
1. Clone the [Fides repo](https://github.com/ethyca/fides)

## Local Setup

1. Spin up the Postgres database with your desired credentials
1. `cd fidesapi/`
1. Update the `application.conf` in `src/main/resources/` with the database credentials
1. `sbt flywayMigrate`
1. `sbt ~jetty:start` -> You now have a Fides Server instance up and running powered by Postgres!
1. In a new shell -> `cd fidesctl/ && pip install -e .`
1. Set the `FIDES_SERVER_URL` environment variable to `localhost:8080` and restart your shell as needed
1. Set the `FIDES_CONFIG_PATH` environment variable and write a config based off of the `fidesctl/example_config.ini`, changing fields as needed.
1. You can now run `fidesctl ping` to verify that your installation is set up properly

## Next Steps

See the [Tutorial](../tutorial.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
