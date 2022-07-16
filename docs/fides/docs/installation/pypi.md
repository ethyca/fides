# Installation from PyPI

This page describes installations using the `fidesctl` package [published on PyPI](https://pypi.org/project/fidesctl/).

## Basic Installation

The Fides team recommends using [`pipx`](https://pypa.github.io/pipx/) over `pip` for environment isolation. The following documentation assumes `pipx` is installed, but `pip` commands can be substituted when needed.
  
To install Fidesctl, run:

`pipx install fidesctl`

## Installing Optional Dependencies

Fidesctl ships with a number of optional dependencies that extend its functionality. To install these, use the following syntax:

`pipx install "fidesctl[extra_1]"`

or

`pipx install "fidesctl[extra_1, extra_2]"`

The optional dependencies are as follows:

* `all`: includes all of the optional dependencies except for `mssql` due to platform-specific issues.
* `aws`: includes the boto3 package to connect to AWS.
* `mssql`: includes the MSSQL database connector.
* `mysql`: includes the MySQL database connector.
* `postgres`: includes the Postgres database connector.
* `redshift`: includes the Redshift database connector.
* `snowflake`: includes the Snowflake database connector.

**NOTE:** When installing database adapters there may be other dependencies, such as the [pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) file that usually requires a Postgres installation or the [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server)

**Apple M1 users of MSSQL:** Known issues around connecting to MSSQL exist today, please reference the following issue for potential solutions: <https://github.com/mkleehammer/pyodbc/issues/846>
