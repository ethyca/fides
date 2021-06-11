# Getting Started

The easiest way to get started with Fides is to pull the [GitHub Repo]() and launch it using the supplied `make` commands. The prerequisites are as follow:

1. Install `Make`
1. Install `Docker`

Once you have those installed, run `make cli`. This will spin up the database, build and set up the server, then start a shell inside of a docker container with `fidesctl` loaded so you can start testing out commands. Run the following commands to become more familiar with `Fides`:

* `fidesctl connect`
* `fidesctl show data-category`
* `fidesctl apply data/sample/`
* `fidesctl apply data/sample/`, This second run confirms nothing has changed
