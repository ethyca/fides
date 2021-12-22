# Installation from PyPI

This page describes installations using the `fidesctl` package [published on PyPI](https://pypi.org/project/fidesctl/).

## Basic Installation

To install Fidesctl, run:

`pip install fidesctl`

With the default installation fidesctl is designed to be as lightweight as possible. It ships with the ability to do most things you would do via the standalone CLI, such as `evaluate` and `parse` without the need to run a webserver. For interacting directly with databases and running the webserver, see the optional dependencies below.

## Installing Optional Dependencies

Fidesctl ships with a number of optional dependencies that extend its functionality. To install these, use the following syntax:

`pip install "fidesctl[extra_1, extra_2]"`

The optional dependencies are as follows:

* `webserver`: includes FastAPI and the Postgres database connector. Enables `fidesctl webserver`.
* `postgres`: includes the Postgres database connector.
* `mysql`: includes the MySQL database connector.
* `mssql`: includes the MSSQL database connector.
* `all`: includes all of the optional dependencies.

**NOTE:** When installing database adapters there may be other dependencies, such as the [pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) file that usually requires a Postgres installation or the [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server)

**Apple M1 users of MSSQL:** Known issues around connecting to MSSQL exist today, as a workaround the following steps may be required if not already completed (`2.3.9_1` current version at time of writing)
```bash
brew install unixodbc
export LDFLAGS="-L/opt/homebrew/Cellar/unixodbc/2.3.9_1/lib"
export CPPFLAGS="-I/opt/homebrew/Cellar/unixodbc/2.3.9_1/include"
```
