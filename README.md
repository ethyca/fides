# Fides

[![License](https://img.shields.io/:license-Apache%202-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0.txt)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Getting Started With Fides

1. Install Docker and Make
1. Clone the `https://gitlab.com/ethyca/fides-core` repo
1. Run `make init-db` in the top-level directory to prepare the database
1. `make cli` to start a shell within a `Fides CLI` container
1. Wait a minute or so for the server to be available, you can check this with `fidesctl connect`
1. `fidesctl` to get a list of possible commands

---

## Glossary

The following is a list of Fides primitives and their definitions

* data-category - A taxonomy of the category that the data is in, i.e. `Account data` or `End-user contact data`.
* data-subject-category - A taxonomy of the type of individual the data is coming from, i.e. `Customer` or `Job Applicant`.
* data-qualifier - A taxonomy of the privacy level of the data. Goes from least dangerous (Anonymized) to most dangerous (Identified).
* data-use - A taxonomy that describes how data is used within a system, i.e. `Train AI System` or `Market/Advertise/Promote`.
* organization - Every object must be assigned to an organization.
* policy - A collection of policy rules.
* policy-rule - A compliance rule defining what action to take when certain combinations of data objects are used.
* registry - A collection of systems.
* system - A complete service/application privacy manifest within an organization.
* user - A Fides User, assigned a role and organization within Fides.
* dataset - A representation of a complete datasource or schema
* dataset-table - A single table or collection within a specified datasource
* dataset-field - A single field within a specified dataset-table

---

## Configuring Fides

### Application Variables

These are the environment variables that can be set to configure the CLI for a specific deployment:

* FIDES_SERVER_URL - The URL of the Fides webserver

### Manifests

Fides ships with default data taxonomies that include standard examples, but in practice you may need to create your own to match what your organization uses in practice. This is done in the same way as declaring other objects. The following is a list of steps to both define and validate new systems within Fides.

#### Creating objects

1. Create the necessary objects (reference the sample manifest files in the `fides_cli/data/samples/`)
1. `fidesctl apply <manifest_dir>/` to create the objects defined in that directory. This will create all objects _except_ for any systems contained within the manifest files.

## Rating your Systems

With your manifests defined, the next step is to “submit” your system for approval or rejection. This is done using the `fidesctl rate <path_to_system_manifests> <policy_id>` command. This will return an object that shows the status of the rating.

## Deployment

The easiest way to deploy Fides is with `pip` for the CLI and `Docker` for the Server and DB.

1. spin up the db
1. `pip install fidesctl`
1. Run the server via it's docker container (`registry.gitlab.com/ethyca/fides-core/fides-server:latest`), injecting the expected env vars for the database connection

---

## Contributing

There are two components to the Fides project; the CLI and the Server. The CLI is a Python application and the Server is a Scala application powered by MySQL.

### Docker Quickstart

To get the whole project up and running via the included docker-compose file, follow these steps:

1. `make init-db` - This will get the database set up and run the migrations.  
1. `make cli` - This will spin up the entire application (DB, Server and CLI) and give you access to a shell inside of the CLI container to interact with the Server.

### Locally-installed Quickstart (Not Recommended)

#### Getting the Server up and running

1. Install [sbt](https://docs.scala-lang.org/getting-started/sbt-track/getting-started-with-scala-and-sbt-on-the-command-line.html). sbt requires at least java version 8. This project works on any java version >= 8.
1. `cd` into the `fides-server` directory
1. Edit the values in src/main/resources/application.conf.example. Any values set here will override the values set in src/main/resources/reference.conf
1. sbt ~jetty:start
1. Endpoints should now be available @ `http://localhost:8080`
1. Current mapping of endpoints can be seen @ src/main/scala/ScalatraBootstrap
1. Current structure of domain objects can be seen with `sbt test:runMain devtools.Generators`

#### Getting the CLI up and running

1. Install Python 3.9
1. Install pip version 21.1 or newer
1. `cd` into the `fides_cli` directory
1. Run `pip install -e .` to have a local installation of the Fides CLI
1. Run `fidesctl` to see a list of commands and a help message

### sbt tasks

Tasks used with sbt for the Server

* `scalafmtAll`: format all files, including tests
* `slickCodegen`: (re)generate slick db table models from database
* `flywayMigrate`: runs flyway database migrations
* `assembly`: builds a standalone jar at target/scala-2.13/fides-server-assembly-VERSION-SNAPSHOT.jar
all other sbt tasks are standard. For a list, `sbt tasks`

### Testing

There are a few different commands you can use to run tests and verify your project.

1. `sbt test` - Used if running the project locally or from with a Server ccontainer shell
1. `make server-test` - Spins up a Docker instance to run the sbt tests
1. `make cli-check-all` - Runs linters, type-checkers and tests against the CLI inside of a Docker container

#### Notes

If you see the docker error `failed to authorize: rpc error: code = Unknown desc = failed to fetch oauth token: unexpected status: 401 Unauthorized` make sure you do not have buildkit enabled.
