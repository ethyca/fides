# Development Overview

---

Thanks for contributing to Fidesops! This section of the docs is designed to help you become familiar with how we work, the standards we apply, and how to ensure your contribution is successful.

If you're stuck, don't be shy about asking for help [on GitHub](https://github.com/ethyca/fidesops/issues).

## Getting Started with Fidesops in Docker

The recommended way to run Fidesops is to launch it with Docker and Docker Compose. `Make` commands wrap docker-compose 
commands to give you different functionality.

### System Requirements 

1. Install Docker: https://docs.docker.com/desktop/#download-and-install
2. Install `make` locally (see Make on Homebrew (Mac), Make for Windows, or your preferred installation) 
   1. `brew install make`
3. Clone fidesops `git clone https://github.com/ethyca/fidesops.git`
4. `cd fidesops`

### Available make commands
- `make server` - this spins up the Fastapi server and supporting resources (a Postgres database and a Redis cache), which you can visit at `http://0.0.0.0:8080`. Check out the docs at `http://0.0.0.0:8000/fidesops/`
- `make integration-env` - spins up everything in make server, plus additional postgres, mongo, and mysql databases for you to execute privacy requests against.
    - Try this out locally with our [Fidesops Postman Collection](../postman/Fidesops.postman_collection.json)
- `make black`, `make mypy`, and `make pylint` - auto-formats code
- `make check-all` - runs the CI checks locally and verifies that your code meets project standards
- `make server-shell`-  opens a shell on the Docker container, from here you can run useful commands like:
  - `ipython` - open a Python shell
- `make pytest` - runs all unit tests except those that talk to integration databases
- `make pytest-integration-access` - runs access integration tests
- `make reset-db` - tears down the Fideops postgres db, then recreates and re-runs migrations.
- `make quickstart` - runs a quick, five second quickstart that talks to the Fidesops API to execute privacy requests
- `make check-migrations` - verifies there are no un-run migrations 
- `make docs-serve` - spins up just the docs

see [Makefile](../../../../Makefile) for more options. 


#### Issues 
When running `make server`, if you get a `importlib.metadata.PackageNotFoundError: fidesops`, do `make server-shell`,
and then run `pip install -e .`. Verify Fidesops is installed with `pip list`. 


### Write your code

We have no doubt you can write amazing code! However, we want to help you ensure your code plays nicely with the rest of the Fides ecosystem. Many projects describe code style and documentation as a suggestion; in Fides it's a CI-checked requirement.

* To learn how to style your code, see the [style guide](code_style.md).
* To learn how to document your code, see the [docs guide](documentation.md).
* To learn how to test your code, see the [tests guide](testing.md).
* To learn what format your PR should follow, make sure to follow the [pull request guidelines](pull_requests.md).

### Submit your code

In order to submit code to Fidesops, please:

* [Fork the Fidesops repository](https://help.github.com/en/articles/fork-a-repo)
* [Create a new branch](https://help.github.com/en/desktop/contributing-to-projects/creating-a-branch-for-your-work) on your fork
* [Open a Pull Request](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) once your work is ready for review
* Once automated tests have passed, a maintainer will review your PR and provide feedback on any changes it requires to be approved. Once approved, your PR will be merged into Fides.

### Congratulations

You're a Fides contributor - welcome to the team! 🎉
