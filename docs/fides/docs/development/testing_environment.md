# Testing Environment

To facilitate thorough manual testing of the application, there is a comprehensive testing environment that can be set up via a single `nox` command.

## Secrets Management

Before being able to spin up the environment, you'll need to grab the `.env` file from 1Password, called `Fides .env`. Download that file and place it in your root directory. This file is ignored by git and therefore safe to keep in your local repo during development.

## Spinning up the Environment

Running `nox -s test_env` will spin up a comprehensive testing environment that does the following:

1. Builds the Webserver, Admin UI and Privacy Center.
1. Downloads all required images.
1. Spins up the entire application, including external Docker-based datastores.
1. Runs various commands and scripts to seed the application with example data, create a user, etc.
1. Opens a shell with the CLI loaded and available for use.

Just before the shell is opened, a `Fides Test Environment` banner will be displayed along with various information about the testing environment and how to access various parts of the application.

From here, everything has been configured and you may commence testing.
