# Contributing

---

We welcome issues, contributions and discussion from all users, regardless of background or experience level. In order to create a positive and welcoming environment, all interactions are governed by Fides's [Code of Conduct](../community/code_of_conduct.md).

## Developing the Server

1. Install [sbt](https://docs.scala-lang.org/getting-started/sbt-track/getting-started-with-scala-and-sbt-on-the-command-line.html). sbt requires at least java version 8. This project works on any java version >= 8.
1. `cd` into the `fidesapi` directory
1. Edit the values in src/main/resources/application.conf.example. Any values set here will override the values set in src/main/resources/reference.conf
1. sbt ~jetty:start
1. Endpoints should now be available @ `http://localhost:8080`
1. Current mapping of endpoints can be seen @ src/main/scala/ScalatraBootstrap
1. Current structure of domain objects can be seen with `sbt test:runMain devtools.Generators`

### Scala Tasks

Tasks used with sbt for the Server

* `scalafmtAll`: format all files, including tests
* `slickCodegen`: (re)generate slick db table models from database
* `flywayMigrate`: runs flyway database migrations
* `assembly`: builds a standalone jar at target/scala-2.13/fidesapi-assembly-VERSION-SNAPSHOT.jar
all other sbt tasks are standard. For a list, `sbt tasks`

## Developing the CLI

1. Install Python 3.8
1. Install pip version 21.1 or newer
1. `cd` into the `fides_cli` directory
1. Run `pip install -e .` to have a local installation of the Fides CLI
1. Run `fidesctl` to see a list of commands and a help message

### Python Tasks

There are a few different commands you can use to run tests and verify your project.

1. Black - `make cli-format`
1. Pylint - `make cli-lint`
1. MyPy - `make cli-typecheck
1. Pytest - `make cli-test
1. All of the above ^ - `make cli-check-all`

## Notes

If you see the docker error `failed to authorize: rpc error: code = Unknown desc = failed to fetch oauth token: unexpected status: 401 Unauthorized` make sure you do not have buildkit enabled.
