# Installation from PyPI

This page describes installations using the `fidesctl` package [published on PyPI](https://pypi.org/project/fidesctl/).

## Installation Tools

Only `pip` installation is currently officially supported.

While there are some successes with using other tools like poetry or pip-tools, they do not share the same workflow as pip - especially when it comes to constraint vs. requirements management. Installing via Poetry or pip-tools is not currently supported. If you wish to install fidesctl using those tools you do so at your own discretion.

## Basic Installation

To install Fidesctl, run:

`pip install fidesctl`

With the default installation fidesctl is designed to be as lightweight as possible. It ships with the ability to do most things you would do via the standalone CLI, such as `evaluate` and `parse` without the need to run a webserver. For interacting directly with databases and running the webserver, see the optional dependencies below.

## Installing Optional Dependencies

Fidesctl ships with a number of optional dependencies that extend its functionality. To install these, use the following syntax:

`pip install "fidesctl[extra_1, extra_2]"`

The optional dependencies are as follows:

* `all`: includes all of the optional dependencies.
* `webserver`: includes FastAPI and the Postgres database connector. Enables `fidesctl webserver`.
* `postgres`: includes the Postgres database connector.
* `mysql`: includes the MySQL database connector.
