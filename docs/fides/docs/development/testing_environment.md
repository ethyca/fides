# Testing Environment

## Quickstart
1. Use `nox -s "fides_env(test)"` to launch the test environment
2. Read the terminal output for details
3. Customize Fides ENV variables by editing `.env`

## Overview

To facilitate thorough manual testing of the application, there is a comprehensive testing environment that can be set up via a single `nox` command: `nox -s "fides_env(test)"`.

This test environment includes:
* Fides Server
* Fides Admin UI
* Fides Postgres Database & Redis Cache
* Sample "Cookie House" Application
* Test Postgres Database
* Test Redis Database
* Sample Resources
* Sample Connectors
* etc.

This test environment is exactly the same environment that users can launch themselves using `fides deploy up`, and you can find all the configuration and settings in `src/fides/data/sample_project`.

## Configuration

There are two ways to configure the `fides` server and CLI:
1. Editing the ENV file in the project root: `.env`
2. Editing the TOML file in the sample project files: `src/fides/data/sample_project/fides.toml`

The `.env` file is safest to add secrets and local customizations, since it is `.gitignore`'d and will not be accidentally committed to version control.

The `fides.toml` file should be used for configurations that should be present for all users testing out the application.

## Advanced Usage

The environment will work "out of the box", but can also be configured to enable other features like S3 storage, email notifications, etc.

To configure these, you'll need to edit the `.env` file and provide some secrets - see `example.env` for what is supported.

## Automated Cypress E2E Tests

The test environment is also used to run automated end-to-end (E2E) tests via Cypress. Use `nox -s e2e_test` to run this locally.