# Running Fides Locally

Fides can also be spun up locally without relying on Docker or Make, however there are significantly more prerequisites.

## Local Requirements

1. Python 3.8
1. pip Version 21 or later
1. Java 8
1. sbt Version 2.12
1. MySQL DB Version 8
1. Clone the [Fides repo](https://github.com/ethyca/fides)

## Local Setup

1. Spin up the MySQL database with your desired credentials
1. `cd fidesapi/`
1. Update the `application.conf` in `src/main/resources/` with the database credentials
1. `sbt flywayMigrate`
1. `sbt ~jetty:start` -> You now have a Fides Server instance up and running powered by MySQL!
1. In a new shell -> `pip install fidesctl`
1. Set the `FIDES_SERVER_URL` environment variable to `localhost:8080`
1. You can now run `fidesctl ping` to verify that your installation is set up properly

## Next Steps

See the [Tutorial](../tutorial.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
