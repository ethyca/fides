# Installation from PyPI

The `fides` Python package is [published on PyPI](https://pypi.org/project/fides/) and maintained by the Fides team. To decide if a PyPI installation is right for your use case, see the [installation overview](./overview.md).

## System requirements

See the the [Prerequisites and Dependencies](../installation/prerequisites.md) page for more information.

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


### Install optional dependencies

Fides ships with a number of optional dependencies that extend its functionality. To install these, use the following syntax:

```sh
pipx install "fides[extra_1]"
```

For multiple dependencies:

```sh
pipx install "fides[extra_1, extra_2]"
```


The optional dependencies are as follows:

* `all`: includes all of the optional dependencies except for `mssql` due to platform-specific issues.
* `aws`: includes the boto3 package to connect to AWS.
* `mssql`: includes the MSSQL database connector.
* `mysql`: includes the MySQL database connector.
* `postgres`: includes the Postgres database connector.
* `redshift`: includes the Redshift database connector.
* `snowflake`: includes the Snowflake database connector.

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
Once Fides is installed and initialized, it is possible to run the project in "standalone mode," which requires zero dependencies outside of Python. This does not provide webserver connectivity, but allows you to experiment with local evaluation commands in the CLI. 

Use one of the following methods to enable standalone mode:

```sh title="CLI flag"
fidesctl --local <subcommand>
```

```toml title="fides.toml"
[cli]
local_mode = true
```
## Database installation

Configure your own Postgres database according to the configuration of your choice, ensuring it satisfies the project [Requirements](./prerequisites.md).

### Generate a connection string
Use your database credentials to generate a [SQLAlchemy Connection String](https://docs.sqlalchemy.org/en/14/core/engines.html#postgresql) in the form of `dialect+driver://username:password@host:port/database`. This will be used as your `database_url` [Configuration](./configuration/configuration.md) variable, or as individual credentials (`name`, `port`, etc).

## Configuring Fides

Fides provides a `fides.toml` file to store your configuration settings. Initializing Fides creates this file and populates it with default values.

See the [Configuration guide](../installation/configuration.md) for a full list of settings.

## Running the webserver

Now that we've spun up our database and set our configuration values, it's time to start our webserver. In a shell, run the following command:

```sh
fidesctl webserver
```

The fidesctl webserver will now be accessible at `localhost:8080`, you can test this by going to `localhost:8080/api/v1/health` and `localhost:8080/docs`.

## Using the CLI

Now that the database and webserver are running, it's time to verify that the whole installation is working properly. Run the command `fidesctl status` to make sure that the CLI can talk to the webserver. The output should look something like this:

```txt
root@2da501a72f8f:/fides/fidesctl# fidesctl status
Getting server status...
Server is reachable and the client/server application versions match.
```

That's it! Your local installation of fidesctl is completely up and running.