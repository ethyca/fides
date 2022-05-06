# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/)

The types of changes are:

* `Added` for new features.
* `Changed` for changes in existing functionality.
* `Developer Experience` for changes in developer workflow or tooling.
* `Deprecated` for soon-to-be removed features.
* `Docs` for documentation only changes.
* `Removed` for now removed features.
* `Fixed` for any bug fixes.
* `Security` in case of vulnerabilities.

## [Unreleased](https://github.com/ethyca/fides/compare/1.6.0...main)

### Added

* Added dependabot to keep dependencies updated
* Include a warning for any orphan datasets as part of the `apply` command.

### Developer Experience

* Added Nox as an alternative to Make

### Docs

* Updated `Release Steps`

### Fixed

* Resolved a failure with populating applicable data subject rights to a data map

## [1.6.0](https://github.com/ethyca/fides/compare/1.5.3...1.6.0) - 2022-05-02

### Added

* CHANGELOG.md file
* On API server startup, in-use config values are logged at the DEBUG level
* Send a usage analytics event upon execution of the `fidesctl init` command

### Developer Experience

* added isort as a CI check
* Include `tests/` in all static code checks (e.g. `mypy`, `pylint`)

### Changed

* Published Docker image does a clean install of Fidesctl
* `with_analytics` is now a decorator

### Fixed

* Third-Country formatting on Data Map
* Potential Duplication on Data Map
* Exceptions are no longer raised when sending `AnalyticsEvent`s on Windows
* Running `fidesctl init` now generates a `server_host` and `server_protocol`
  rather than `server_url`
