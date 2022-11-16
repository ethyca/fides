# Installation from PyPI

The Fides Python package is [published on PyPI](https://pypi.org/project/fides/) and maintained by the Fides team. To decide if a PyPI installation is right for your use case, see the [installation overview](./overview.md).

## System requirements

See the the [Prerequisites and Dependencies](../installation/requirements.md) page for more information.

## Basic installation

The Fides team recommends using [`pipx`](https://pypa.github.io/pipx/) over `pip` for environment isolation. The following documentation assumes `pipx` is installed, but `pip` commands can be substituted when needed.
  
To install Fides, run:

```sh
pipx install fides
```

### Verify your installation

With Fides installed, verify the installation:

```sh
fides --version
```

A correct installation will print the current version of Fides to your console.

### Install dangerous dependencies

Fides is designed to ship with all possible dependencies, however there are some packages which may break on certain machines. To solve this, Fides supports optional requirements for potentially dangerous dependencies that aren't required to run the application, but may restrict certain functionality.

To install optional dependencies, use the following syntax:

```sh
pipx install "fides[extra_1]"
```

For multiple dependencies:

```sh
pipx install "fides[extra_1, extra_2]"
```

The optional "dangerous" dependencies are as follows:

* `mssql`: includes the MSSQL database connector.

When installing database adapters, additional dependencies may be required (e.g. [pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) for Postgres, or the [Microsoft ODBC Driver](https://docs.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server) for SQL Server).

!!! Warning "Apple M1 users of MSSQL"
     Known issues around connecting to MSSQL exist today, please reference the following issue for potential solutions: <https://github.com/mkleehammer/pyodbc/issues/846>

## Initialize Fides

Initializing the project will create a configuration file with default values, and generate a directory to house your Fides resources.

```sh title="Initialize Fides"
fides init
```

```txt title="Expected Output"
Initializing Fides...
----------
Created a './.fides' directory.
----------
Created a fides config file: ./.fides/fides.toml
To learn more about configuring fides, see:
    https://ethyca.github.io/fides/installation/configuration/
----------
For example policies and help getting started, see:
    https://ethyca.github.io/fides/guides/policies/
----------
Fides initialization complete.
```

### Run standalone mode

Once Fides is installed and initialized, it is possible to run the project in "standalone mode," which requires zero dependencies outside of the pip installation. This does not provide webserver connectivity or database persistence, but allows you to experiment with CLI commands.

Use one of the following methods to enable standalone mode:

```sh title="CLI flag"
fides --local <subcommand>
```

```toml title="fides.toml"
[cli]
local_mode = true
```

## Set up your database

Configure your own Postgres database according to the configuration of your choice, ensuring it satisfies the project [requirements](./requirements.md). Enable a username and password, and keep track of your connection credentials.

## Set up your cache

Configure your own Redis cache according to the configuration of your choice, ensuring it satisfies the project [requirements](./requirements.md). Enable a password (via Redis [`AUTH`](https://redis.io/commands/auth)) to provide additional security, and keep track of your connection credentials.

## Configure Fides

Fides provides a `fides.toml` file to store your configuration settings. Initializing Fides creates this file and populates it with default values, which should be replaced with the connection credentials for your Postgres and Redis instances, as well as any other information unique to your deployment.

See the [Configuration guide](../installation/configuration.md) for a full list of settings, and a sample `fides.toml`.

## Running the webserver

In a shell, run the following command:

```sh
fides webserver
```

With the Fides webserver running, the hosted UI is available at `http://{server_url}/` (e.g. `http://localhost:8080/`).
