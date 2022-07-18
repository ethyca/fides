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

## [Unreleased](https://github.com/ethyca/fides/compare/1.7.0...main)

### Added

* Add datasets via YAML in the UI [#813](https://github.com/ethyca/fides/pull/813)
* Add datasets via database connection [#834](https://github.com/ethyca/fides/pull/834) [#889](https://github.com/ethyca/fides/pull/889)
* Add delete confirmation when deleting a field or collection from a dataset [#809](https://github.com/ethyca/fides/pull/809)
* Add ability to delete datasets from the UI
* Initial configuration wizard UI view
  * System scanning step: AWS credentials form and initial `generate` API usage.
  * System scanning results: AWS systems are stored and can be selected for review
* Added Cypress for testing [713](https://github.com/ethyca/fides/pull/833)
* CustomInput type "password" with show/hide icon.
* Pull CLI command now checks for untracked/unstaged files in the manifests dir [#869](https://github.com/ethyca/fides/pull/869)
* Pull CLI command has a flag to pull missing files from the server [#895](https://github.com/ethyca/fides/pull/895)
* Add Okta support to the `/generate` endpoint [#842](https://github.com/ethyca/fides/pull/842)
* Add db support to `/generate` endpoint [849](https://github.com/ethyca/fides/pull/849)
* Add BigQuery support for the `generate` cli command [#814](https://github.com/ethyca/fides/pull/814)
* Added OpenAPI TypeScript client generation for the UI app. See the [README](/clients/admin-ui/src/types/api/README.md) for more details.
* Added user auth tables [915](https://github.com/ethyca/fides/pull/915)
* Standardized API error parsing under `~/types/errors`
* Added taxonomy page to UI [#902](https://github.com/ethyca/fides/pull/902)

### Changed

* Updated the `datamap` endpoint to return human-readable column names as the first response item [#779](https://github.com/ethyca/fides/pull/779)
* Remove the `obscure` requirement from the `generate` endpoint [#819](https://github.com/ethyca/fides/pull/819)
* Moved all files from `fidesapi` to `fidesctl/api` [#885](https://github.com/ethyca/fides/pull/885)
* Moved `scan` and `generate` to the list of commands that can be run in local mode [#841](https://github.com/ethyca/fides/pull/841)
* Webserver dependencies now come as a standard part of the package [#881](https://github.com/ethyca/fides/pull/881)
* Initial configuration wizard UI view
  * Refactored step & form results management to use Redux Toolkit slice.
* Change `id` field in tables from an integer to a string [915](https://github.com/ethyca/fides/pull/915)
* Update `fideslang` to `1.1.0`, simplifying the default taxonomy and adding `tags` for resources [#865](https://github.com/ethyca/fides/pull/865)
* Remove the `obscure` requirement from the `generate` endpoint [#819](https://github.com/ethyca/fides/pull/819)

### Docs

* recommend/replace pip installs with pipx [#874](https://github.com/ethyca/fides/pull/874)

### Fixed

* CustomSelect input tooltips appear next to selector instead of wrapping to a new row.
* Datasets without the `third_country_transfer` will not cause the editing dataset form to not render.
* Fixed a build issue causing an `unknown` version of `fidesctl` to be installed in published Docker images [#836](https://github.com/ethyca/fides/pull/836)
* Fixed an M1-related SQLAlchemy bug [#816](https://github.com/ethyca/fides/pull/891)
* Endpoints now work with or without a trailing slash. [#886](https://github.com/ethyca/fides/pull/886)
* Dataset field columns show all columns by default in the UI [#898](https://github.com/ethyca/fides/pull/898)
* Fixed the `tag` specific GitHub Action workflows for Docker and publishing docs. [#901](https://github.com/ethyca/fides/pull/901)

## [1.7.0](https://github.com/ethyca/fides/compare/1.6.1...1.7.0) - 2022-06-23

### Added

* Added dependabot to keep dependencies updated
* A warning now issues for any orphan datasets as part of the `apply` command [543](https://github.com/ethyca/fides/pull/543)
* Initial scaffolding of management UI [#561](https://github.com/ethyca/fides/pull/624)
* A new `audit` command for `system` and `organization` resources, checking data map attribute compliance [#548](https://github.com/ethyca/fides/pull/548)
* Static UI assets are now built with the docker container [#663](https://github.com/ethyca/fides/issues/663)
* Host static files via fidesapi [#621](https://github.com/ethyca/fides/pull/621)
* A new `generate` endpoint to enable capturing systems from infrastructure from the UI [#642](https://github.com/ethyca/fides/pull/642)
* A new `datamap` endpoint to enable visualizing a data map from the UI [#721](https://github.com/ethyca/fides/pull/721)
* Management UI navigation bar [#679](https://github.com/ethyca/fides/issues/679)
* Management UI integration [#736](https://github.com/ethyca/fides/pull/736)
  * Datasets
  * Systems
  * Taxonomy (data categories)
* Initial dataset UI view [#768](https://github.com/ethyca/fides/pull/768)
  * Add interaction for viewing a dataset collection
  * Add column picker
  * Add a data category checklist tree
  * Edit/delete dataset fields
  * Edit/delete dataset collections
  * Edit datasets
  * Add a component for Identifiability tags
  * Add tooltips for help on forms
  * Add geographic location (third_country_transfers) country selection. Supported by new dependency `i18n-iso-countries`.
* Okta, aws and database credentials can now come from `fidesctl.toml` config [#694](https://github.com/ethyca/fides/pull/694)
* New `validate` endpoint to test aws and okta credentials [#722](https://github.com/ethyca/fides/pull/722)
* Initial configuration wizard UI view
  * Manual entry steps added (name and describe organization, pick entry route, and describe system manually including privacy declarations)
* A new image tagged `ethyca/fidesctl:dev` is published on each push to `main` [781](https://github.com/ethyca/fides/pull/781)
* A new cli command (`fidesctl sync`) [#765](https://github.com/ethyca/fides/pull/765)

### Changed

* Comparing server and CLI versions ignores `.dirty` only differences, and is quiet on success when running general CLI commands [621](https://github.com/ethyca/fides/pull/621)
* All endpoints now prefixed by `/api/v1` [#623](https://github.com/ethyca/fides/issues/623)
* Allow AWS credentials to be passed to `generate system` via the API [#645](https://github.com/ethyca/fides/pull/645)
* Update the export of a datamap to load resources from the server instead of a manifest directory [#662](https://github.com/ethyca/fides/pull/662)
* Refactor `export` to remove CLI specific uses from the core modules and load resources[#725](https://github.com/ethyca/fides/pull/725)
* Bump version of FastAPI in `setup.py` to 0.77.1 to match `optional-requirements.txt` [#734](https://github.com/ethyca/fides/pull/734)
* Docker images are now only built and pushed on tags to match when released to pypi [#740](https://github.com/ethyca/fides/pull/740)
* Okta resource scanning and generation now works with systems instead of datasets [#751](https://github.com/ethyca/fides/pull/751)

### Developer Experience

* Replaced `make` with `nox` [#547](https://github.com/ethyca/fides/pull/547)
* Removed usage of `fideslang` module in favor of new [external package](https://github.com/ethyca/fideslang) shared across projects [#619](https://github.com/ethyca/fides/issues/619)
* Added a UI service to the docker-compose deployment [#757](<https://github.com/ethyca/fides/pull/757>)
* `TestClient` defined in and shared across test modules via `conftest.py` [#759](https://github.com/ethyca/fides/pull/759)

### Docs

* Replaced all references to `make` with `nox` [#547](https://github.com/ethyca/fides/pull/547)
* Removed config/schemas page [#613](https://github.com/ethyca/fides/issues/613)
* Dataset UI and config wizard docs added (<https://github.com/ethyca/fides/pull/697>)
* The fides README now walks through generating a datamap [#746](https://github.com/ethyca/fides/pull/746)

### Fixed

* Updated `fideslog` to v1.1.5, resolving an issue where some exceptions thrown by the SDK were not handled as expected [#609](https://github.com/ethyca/fides/issues/609)
* Updated the webserver so that it won't fail if the database is inaccessible [#649](https://github.com/ethyca/fides/pull/649)
* Updated external tests to handle complex characters [#661](https://github.com/ethyca/fides/pull/661)
* Evaluations now properly merge the default taxonomy into the user-defined taxonomy [#684](https://github.com/ethyca/fides/pull/684)
* The CLI can now be run without installing the webserver components [#715](https://github.com/ethyca/fides/pull/715)

## [1.6.1](https://github.com/ethyca/fides/compare/1.6.0...1.6.1) - 2022-06-15

### Docs

* Updated `Release Steps`

### Fixed

* Resolved a failure with populating applicable data subject rights to a data map
* Handle invalid characters when generating a `fides_key` [#761](https://github.com/ethyca/fides/pull/761)

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
