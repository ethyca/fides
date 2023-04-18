# Development Overview

Thanks for contributing to Fides! This section of the docs is designed to help you become familiar with how we work, the standards we apply, and how to ensure your contribution is successful.

If you're stuck, don't be shy about asking for help [on GitHub](https://github.com/ethyca/fides/issues).

## Getting Started

The first step is to clone the Fides repo for development:

```bash
git clone https://github.com/ethyca/fides
```

Once that's complete, there are a few different tools to install for get everything up and running.

## Tool Installation

The primary requirements for contributing to Fides are `Docker` and `Python`. The download links as well as minimum required versions are provided below:

* [Docker](https://www.docker.com/products/docker-desktop) (version 20.10.11 or later)
* [Python](https://www.python.org/downloads/) (version 3.8 through 3.10)

Now that those are installed, the final step is to download the dev requirements for the Fides project. We recommend doing this in a virtual environment or using [pipx](https://pypa.github.io/pipx/), but that is outside the scope of this guide.

!!!note
    Although it functions "out of the box", there are some additional configuration steps that can be taken on Apple's ARM silicon (M-series chips, i.e. M1, M2, M2 Max, etc.) to make developing with Docker a smoother experience.
    
    1. Increase disk space allocation.

```bash
pip install -r dev-requirements.txt
```

## Development Workflows

Development of Fides is primarily done through utilizing the included `Nox` commands. There is a full guide on development workflows and best practices on the [Developing Fides](developing_fides.md) page.

## Known Issues

* MSSQL: Known issues around connecting to MSSQL exist today for Apple M1 users. M1 users that wish to install `pyodbc` locally, please reference the workaround [here](https://github.com/mkleehammer/pyodbc/issues/846).

* Package not found: When running `nox -s dev`, if you get a `importlib.metadata.PackageNotFoundError: fides`, do `nox -s dev -- shell`, and then run `pip install -e .`. Verify Fides is installed with `pip list`.

### Write your code

We have no doubt you can write amazing code! However, we want to help you ensure your code plays nicely with the rest of the Fides ecosystem. Many projects describe code style and documentation as a suggestion; in Fides it's a CI-checked requirement.

* To learn how to style your code, see the [style guide](code_style.md).
* To learn how to migrate the database schema, see the [database migration guide](database_migration.md).
* To learn how to document your code, see the [docs guide](documentation.md).
* To learn how to test your code, see the [tests guide](testing.md).
* To learn what format your PR should follow, make sure to follow the [pull request guidelines](pull_requests.md).

### Submit your code

In order to submit code to Fides, please:

* [Fork the Fides repository](https://help.github.com/en/articles/fork-a-repo)
* [Create a new branch](https://help.github.com/en/desktop/contributing-to-projects/creating-a-branch-for-your-work) on your fork
* [Open a Pull Request](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) once your work is ready for review
* Once automated tests have passed, a maintainer will review your PR and provide feedback on any changes it requires to be approved. Once approved, your PR will be merged into Fides.

### Congratulations

You're a Fides contributor - welcome to the team! 🎉
