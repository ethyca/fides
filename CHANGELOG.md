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
* Initial scaffolding of management UI [#561](https://github.com/ethyca/fides/pull/624)
* New `audit` command for `system` and `organization` resources, checking data map attribute compliance. [#548](https://github.com/ethyca/fides/pull/548)
* UI static assets are now built with the docker container [#663](https://github.com/ethyca/fides/issues/663)
* Host static files via fidesapi [#621](https://github.com/ethyca/fides/pull/621)
* New `generate` endpoint to enable capturing systems from infrastructure from the UI [#642](https://github.com/ethyca/fides/pull/642)
* New `datamap` endpoint to enable visualizing a data map from the UI [#721](https://github.com/ethyca/fides/pull/721)
* Navigation bar for management UI
* Integration for management UI
  * Datasets
  * Systems
  * Taxonomy (data categories)
* Initial dataset collection UI view
  * Add interaction for viewing a dataset collection
  * Add column picker
  * Add a data category checklist tree  
  * Edit dataset fields
  * Edit dataset collections
  * Add a component for Identifiability tags
* Okta, aws and database credentials can now come from `fidesctl.toml` config [#694](https://github.com/ethyca/fides/pull/694)
* New `validate` endpoint to test aws and okta credentials [#722](https://github.com/ethyca/fides/pull/722)


### Changed

* Comparing server and CLI versions ignores `.dirty` only differences, and is quiet on success when running general CLI commands
* Migrate all endpoints to be prefixed by `/api/v1` [#623](https://github.com/ethyca/fides/issues/623)
* Allow credentials to be passed to the generate systems from aws functionality via the API [#645](https://github.com/ethyca/fides/pull/645)
* Update the export of a datamap to load resources from the server instead of a manifest directory[#662](https://github.com/ethyca/fides/pull/662)
* Refactor `export` to remove CLI specific uses from the core modules and load resources[#725](https://github.com/ethyca/fides/pull/725)
* Bump version of FastAPI in `setup.py` to 0.77.1 to match `optional-requirements.txt` [#734](https://github.com/ethyca/fides/pull/734)
* Docker images are now only built and pushed on tags to match when we release to pypi [#740](https://github.com/ethyca/fides/pull/740)

### Developer Experience

* Replaced `make` with `nox`
* Removed usage of `fideslang` module in favor of new [external package](https://github.com/ethyca/fideslang) shared across projects
* Added starting up the frontend server to `nox`

### Docs

* Updated `Release Steps`
* Replaced all references to `make` with `nox` [#547](https://github.com/ethyca/fides/pull/547)
* Removed config/schemas page [#613](https://github.com/ethyca/fides/issues/613)

### Fixed

* Resolved a failure with populating applicable data subject rights to a data map
* Updated `fideslog` to v1.1.5, resolving an issue where some exceptions thrown by the SDK were not handled as expected
* Updated the webserver so that it won't fail if the database is inaccessible [#649](https://github.com/ethyca/fides/pull/649)
* Handle complex characters in external tests  [#661](https://github.com/ethyca/fides/pull/661)
* Evaluations now properly merge the default taxonomy into the user-defined taxonomy [#684](https://github.com/ethyca/fides/pull/684)
* The CLI can be run without installing the webserver components [#715](https://github.com/ethyca/fides/pull/715)

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
