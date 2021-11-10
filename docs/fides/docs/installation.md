# Installation

## Basic Installation

Fidesctl is tested to be compatible with Python 3.8 and above.

To install Fidesctl, run:

`pip install fidesctl`

With the basic installation fidesctl is designed to be as lightweight as possible. It ships with the ability to do most things you would do via the CLI, such as `apply`, `evaluate`, and `parse`. For interacting directly with databases and running the webserver, see the optional dependencies below.

## Installing Optional Dependencies

Fidesctl ships with a number of optional dependencies that extend its functionality. To install these, use the following syntax:

`pip install "fidesctl[extra_1, extra_2]"`

The optional dependencies are as follows:

* `all`: includes all of the optional dependencies.
* `webserver`: includes FastAPI and the Postgres database connector. Enables `fidesctl webserver`.
* `postgres`: includes the Postgres database connector.
* `mysql`: includes the MySQL database connector.
