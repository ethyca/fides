# Testing Environment

To facilitate thorough manual testing of the application, there is a comprehensive testing environment that can be set up via a single `nox` command.

## Configuration

The environment will configure the `fides` server and CLI using the TOML configuration set in `src/fides/data/test_env/fides.test_env.toml`. To test out other configurations, you can edit this file and reload the test env; however, don't commit these changes unless you are sure that the default configuration for testing should change for everyone!

## Secrets Management

The environment will work "out of the box", but can also be configured with secrets needed to configure other features like S3 storage, Mailgun notifications, etc. To configure this, you'll need to create the `.env` file, place it at the root of the repository directory, and provide some secrets. There is an `example.env` file you can reference to see what secrets are supported.

This `.env` file is ignored by git and therefore safe to keep in your local repo during development.

For Ethyca-internal engineers, you can also grab a fully populated `.env` file from 1Password (called `Fides .env`).

## Spinning up the Environment

Running `nox -s test_env` will spin up a comprehensive testing environment that does the following:

1. Builds the Webserver, Admin UI and Privacy Center.
1. Downloads all required images.
1. Spins up the entire application, including external Docker-based datastores.
1. Runs various commands and scripts to seed the application with example data, create a user, etc.
1. Opens a shell with the CLI loaded and available for use.

Just before the shell is opened, a `Fides Test Environment` banner will be displayed along with various information about the testing environment and how to access various parts of the application.

From here, everything has been configured and you may commence testing.
