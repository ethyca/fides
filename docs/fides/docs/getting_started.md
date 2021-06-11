# Getting Started

This section contains Quick Start guides to help you get up and running with Fides.

## Running Fides in Docker

The easiest way to get started with Fides is to pull the [GitHub Repo](https://github.com/ethyca/fides) and launch it using the supplied `make` commands. The prerequisites are as follow:

1. Install Make
1. Install Docker

Once you have those installed, run `make cli`. This will spin up the database, build and set up the server, then start a shell inside of a docker container with `fidesctl` loaded so you can start testing out commands. Run the following commands to become more familiar with `Fides`:

* `fidesctl connect`
* `fidesctl show data-category`
* `fidesctl apply data/sample/`
* `fidesctl apply data/sample/`, This second run confirms nothing has changed

## Running Fides Locally

Fides can also be spun up locally without relying on Docker.

### Fidesctl Setup

1. Download Python 3.8
1. Run `pip install fidesctl`

### Scala Setup

1. Install Java 8
1. Install sbt version `2.12`

### Server Setup

1. Install and spin up MySQL
