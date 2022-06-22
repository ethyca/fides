# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/)

The types of changes are:

* `Added` for new features.
* `Changed` for changes in existing functionality.
* `Developer Experience` for changes in developer workflow or tooling.
* `Deprecated` for soon-to-be removed features.
* `Breaking Changes` for updates that break public facing APIs
* `Docs` for documentation only changes.
* `Removed` for now removed features.
* `Fixed` for any bug fixes.
* `Security` in case of vulnerabilities.


## [Unreleased](https://github.com/ethyca/fidesops/compare/1.5.3...main)

### Added
* Subject Request Details page [#563](https://github.com/ethyca/fidesops/pull/563)
* Restart Graph from Failure [#578](https://github.com/ethyca/fidesops/pull/578)
* Redis SSL Support [#611](https://github.com/ethyca/fidesops/pull/611)
* Celery as a dependency for use in the execution layer [#610](https://github.com/ethyca/fidesops/pull/610)
* Cache and Surface Resume/Restart Instructions [#591](https://github.com/ethyca/fidesops/pull/591)
* Build and deploy Admin UI from webserver [#625](https://github.com/ethyca/fidesops/pull/625)
* Allow disabling a ConnectionConfig [#637](https://github.com/ethyca/fidesops/pull/637)
* Erasure support for Outreach connector [#619](https://github.com/ethyca/fidesops/pull/619)
* Adds searching of ConnectionConfigs [#641](https://github.com/ethyca/fidesops/pull/641)
* Added `AdminUiSettings` to the `log_all_config_values` helper method [#647](https://github.com/ethyca/fidesops/pull/647)
* Prettier formatting CI check for frontend code [#655](https://github.com/ethyca/fidesops/pull/655)
* Adds default policies [#654](https://github.com/ethyca/fidesops/pull/654)
* Added ConnectionConfig `connection_type` and `disabled` filters [#675](https://github.com/ethyca/fidesops/pull/675)
* Adds Fideslog integration [#541](https://github.com/ethyca/fidesops/pull/541)
* Adds endpoint analytics events [#622](https://github.com/ethyca/fidesops/pull/622)
* Sample dataset and access configuration for Zendesk (ticket endpoints) [#677](https://github.com/ethyca/fidesops/pull/677)
* Include number of records to be masked in masking endpoint's log message [#692](https://github.com/ethyca/fidesops/pull/692)
* Datastore Connection Landing Page [#674](https://github.com/ethyca/fidesops/pull/674)
* Added the ability to delete a datastore from the frontend [#683] https://github.com/ethyca/fidesops/pull/683

### Changed

* Refactor auth and enable static file serving [#577](https://github.com/ethyca/fidesops/pull/577)
* Bumped mypy to version 0.961 [#630](https://github.com/ethyca/fidesops/pull/630)
* Bumped Python to version 3.9.13 in the `Dockerfile` [#630](https://github.com/ethyca/fidesops/pull/630)
* Matched the path to the migrations in the mypy settings with the new location [#634](https://github.com/ethyca/fidesops/pull/634)
* Sort ConnectionConfig by name ascending [#668](https://github.com/ethyca/fidesops/pull/672)
* Install MSSQL By Default [#664] (https://github.com/ethyca/fidesops/pull/664)
* [Admin UI] Change "Policy Name" to "Request Type" on SR list page.[#546](https://github.com/ethyca/fidesops/pull/696)

### Developer Experience

* Add celerybeat-schedule file to gitignore [#639](https://github.com/ethyca/fidesops/pull/639)

### Fixed
* Fixed error with running mypy on M1 Macs [#630](https://github.com/ethyca/fidesops/pull/630)
* Fixed error with mypy on Python versions greater than 3.9.6 [#630](https://github.com/ethyca/fidesops/pull/630)
* Bumped fideslib to 2.0.4. This fixes the issue where alembic couldn't find the `fidesops.toml` file from its new location [#643](https://github.com/ethyca/fidesops/pull/643)

## [1.5.3](https://github.com/ethyca/fidesops/compare/1.5.2...1.5.3)

### Changed
* Database migrations now exist as part of the core `fidesops` package [#620](https://github.com/ethyca/fidesops/pull/620)

### Removed
* The `[package]` config section no longer exists [#620](https://github.com/ethyca/fidesops/pull/620)


## [1.5.2](https://github.com/ethyca/fidesops/compare/1.5.1...1.5.2)

### Added
* Added OAuth2 authentication strategy for SaaS connectors [#555](https://github.com/ethyca/fidesops/pull/555)
* Added `FIDESOPS__SECURITY__LOG_LEVEL` configuration variable to allow controlling the log level [#579](https://github.com/ethyca/fidesops/pull/579)
* Added `DEBUG` logs at startup to view all configuration values [#579](https://github.com/ethyca/fidesops/pull/579)
* Modified `filter` post-processor to include toggles for exact and case sensitive matching [#584](https://github.com/ethyca/fidesops/pull/584)
* Added dataset for Outreach with access configuration [#588](https://github.com/ethyca/fidesops/pull/588)
* All directories containing `*.py` files now also contain `__init__.py` files [#590](https://github.com/ethyca/fidesops/pull/590)
* Pause Erasure Request Execution / Resume on Manual Input in [#571](https://github.com/ethyca/fidesops/pull/571/)

### Changed
* Use the `RuleResponse` schema within the `PrivacyRequestReposnse` schema [#580](https://github.com/ethyca/fidesops/pull/580)
* Updated the webserver to use `PORT` config variable from the `fidesops.toml` file [#586](https://github.com/ethyca/fidesops/pull/586)
* Updated `black-ci` makefile command to also check `tests/` directory [#594](https://github.com/ethyca/fidesops/pull/594)

### Developer Experience
* Adds a script for MSSQL schema exploration [#557](https://github.com/ethyca/fidesops/pull/581)


## [1.5.1](https://github.com/ethyca/fidesops/compare/1.5.0...1.5.1) - 2022-05-27

### Added
* Added `FIDESOPS__DATABASE__ENABLED` and `FIDESOPS__REDIS__ENABLED` configuration variables to allow `fidesops` to run cleanly in a "stateless" mode without any database or redis cache integration [#550](https://github.com/ethyca/fidesops/pull/550)
* Pause Access Request Execution / Resume on Manual Input in [#554](https://github.com/ethyca/fidesops/pull/554)
* A `[package]` section of the `fidesops.toml` configuration file may specify the path to the `fidesops` package itself [#566](https://github.com/ethyca/fidesops/pull/566)

### Changed
* `MaskingStrategyFactory` and associated `MaskingStrategy` implementations now use a decorator-based registration system, to improve extensibility [#560](https://github.com/ethyca/fidesops/pull/560)
* Added `from __future__ import annotations` to `src/fidesops/util/logger.py` to maintain backward compatibility with Python < 3.9 [#569](https://github.com/ethyca/fidesops/pull/569)

### Developer Experience

* Import ordering is now enforced using [isort](https://pycqa.github.io/isort/) in CI [#533](https://github.com/ethyca/fidesops/pull/533)
* Teardown all Docker infra once it's finished with [#498](https://github.com/ethyca/fidesops/pull/498/)
* Update PR checklist for [`CHANGELOG.md`](https://github.com/ethyca/fidesops/blob/main/CHANGELOG.md) file [#558](https://github.com/ethyca/fidesops/pull/558)
* Database migrations are included in the published PyPI package [#566](https://github.com/ethyca/fidesops/pull/566)

### Docs

* Updated documentation for the user management ui [#530](https://github.com/ethyca/fidesops/pull/530)
* Added documentation for the privacy center [#549](https://github.com/ethyca/fidesops/pull/549)

### Fixed

* Fixed type errors for privacy center build [#540](https://github.com/ethyca/fidesops/pull/540)

## [1.5.0](https://github.com/ethyca/fidesops/compare/1.4.2...1.5.0) - 2022-05-18

### Added

* ESLint configuration changes [#514](https://github.com/ethyca/fidesops/pull/514)
* User creation, update and permissions in the Admin UI [#511](https://github.com/ethyca/fidesops/pull/511)
* Yaml support for dataset upload [#284](https://github.com/ethyca/fidesops/pull/284)


### Breaking Changes
* Update masking API to take multiple input values [#443](https://github.com/ethyca/fidesops/pull/443


### Docs

* DRP feature documentation [#520](https://github.com/ethyca/fidesops/pull/520)


## [1.4.2](https://github.com/ethyca/fidesops/compare/1.4.1...1.4.2) - 2022-05-12

### Added

* GET routes for users [#405](https://github.com/ethyca/fidesops/pull/405)
* Username based search on GET route [#444](https://github.com/ethyca/fidesops/pull/444)
* FIDESOPS__DEV_MODE for Easier SaaS Request Debugging [#363](https://github.com/ethyca/fidesops/pull/363)
* Track user privileges across sessions [#425](https://github.com/ethyca/fidesops/pull/425)
* Add first_name and last_name fields. Also add them along with created_at to FidesopsUser response [#465](https://github.com/ethyca/fidesops/pull/465)
* Denial reasons for DSR and user `AuditLog` [#463](https://github.com/ethyca/fidesops/pull/463)
* DRP action to Policy [#453](https://github.com/ethyca/fidesops/pull/453)
* `CHANGELOG.md` file[#484](https://github.com/ethyca/fidesops/pull/484)
* DRP status endpoint [#485](https://github.com/ethyca/fidesops/pull/485)
* DRP exerise endpoint [#496](https://github.com/ethyca/fidesops/pull/496)
* Frontend for privacy request denial reaons [#480](https://github.com/ethyca/fidesops/pull/480)
* Publish Fidesops to Pypi [#491](https://github.com/ethyca/fidesops/pull/491)
* DRP data rights endpoint [#526](https://github.com/ethyca/fidesops/pull/526)


### Changed
* Converted HTTP Status Codes to Starlette constant values [#438](https://github.com/ethyca/fidesops/pull/438)
* SaasConnector.send behavior on ignore_errors now returns raw response [#462](https://github.com/ethyca/fidesops/pull/462)
* Seed user permissions in `create_superuser.py` script [#468](https://github.com/ethyca/fidesops/pull/468)
* User API Endpoints (update fields and reset user passwords) [#471](https://github.com/ethyca/fidesops/pull/471)
* Format tests with `black` [#466](https://github.com/ethyca/fidesops/pull/466)
* Extract privacy request endpoint logic into separate service for DRP [#470](https://github.com/ethyca/fidesops/pull/470)
* Fixing inconsistent SaaS connector integration tests [#473](https://github.com/ethyca/fidesops/pull/473)
* Add user data to login response [#501](https://github.com/ethyca/fidesops/pull/501)


### Breaking Changes
* Update masking API to take multiple input values [#443](https://github.com/ethyca/fidesops/pull/443

### Docs

* Added issue template for documentation updates [#442](https://github.com/ethyca/fidesops/pull/442)
* Clarify masking updates [#464](https://github.com/ethyca/fidesops/pull/464)
* Added dark mode [#476](https://github.com/ethyca/fidesops/pull/476)


### Fixed

* Removed miradb test warning [#436](https://github.com/ethyca/fidesops/pull/436)
* Added missing import [#448](https://github.com/ethyca/fidesops/pull/448)
* Removed pypi badge pointing to wrong package [#452](https://github.com/ethyca/fidesops/pull/452)
* Audit imports and references [#479](https://github.com/ethyca/fidesops/pull/479)
* Switch to using update method on PUT permission endpoint [#500](https://github.com/ethyca/fidesops/pull/500)


### Developer Experience
* Add script to seed initial Privacy Request [#487](https://github.com/ethyca/fidesops/pull/487)
* Add first and last name to `createsuperuser` script [#486](https://github.com/ethyca/fidesops/pull/486)
