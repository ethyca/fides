# Installation from PyPI

This page describes installations using the `fidesctl` package [published on PyPI](https://pypi.org/project/fidesctl/).

## Requirements

1. [Python](https://www.python.org/downloads/) (3.8+)
1. [pipx](https://pypa.github.io/pipx/installation/)

## Basic Installation

To keep fidesctl isolated as an application within it's own environment, we recommend using `pipx` to install `fidesctl`.

1. `pip install pipx ; pipx ensurepath`
1. Restart your shell
1. `pipx install fidesctl`

With the default installation fidesctl is designed to be as lightweight as possible. It ships with the ability to do most things you would do via the standalone CLI, such as `evaluate` and `parse` without the need to run a webserver. For interacting directly with databases and running the webserver, see the optional dependencies below.

## Installing Optional Dependencies

Fidesctl ships with a number of optional dependencies that extend its functionality. To install these, use the following syntax:

`pipx install "fidesctl[extra_1, extra_2]"`

The optional dependencies are as follows:

* `all`: includes all of the optional dependencies except for `mssql` due to platform-specific issues.
* `aws`: includes the boto3 package to connect to AWS.
* `mssql`: includes the MSSQL database connector.
* `mysql`: includes the MySQL database connector.
* `postgres`: includes the Postgres database connector.
* `redshift`: includes the Redshift database connector.
* `snowflake`: includes the Snowflake database connector.
* `webserver`: includes FastAPI and the Postgres database connector. Enables `fidesctl webserver`.

**NOTE:** When installing database adapters there may be other dependencies, such as the [pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) file that usually requires a Postgres installation or the [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server)

**Apple M1 users of MSSQL:** Known issues around connecting to MSSQL exist today, please reference the following issue for potential solutions: <https://github.com/mkleehammer/pyodbc/issues/846>
