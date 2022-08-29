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


## [Unreleased](https://github.com/ethyca/fidesops/compare/1.7.2...main)

### Docs
* Fix analytics opt out environment variable name [#1170](https://github.com/ethyca/fidesops/pull/1170)
* Added how to view a subject request history and reprocess a subject request [#1164](https://github.com/ethyca/fidesops/pull/1164)

## [1.7.2](https://github.com/ethyca/fidesops/compare/1.7.1...1.7.2)

### Added
* Adds users and owners configuration for Hubspot connector [#1091](https://github.com/ethyca/fidesops/pull/1091)
* Foundations for a new email connector type [#1142](https://github.com/ethyca/fidesops/pull/1142)

## [1.7.1](https://github.com/ethyca/fidesops/compare/1.7.0...1.7.1)

### Breaking Changes
The `oauth2` strategy has been renamed to `oauth2_authorization_code` in order to make a distinction between the newly introduced `oauth2_client_credentials` strategy [#1159](https://github.com/ethyca/fidesops/pull/1159)

### Added

* Access support for Datadog Logs [#1060](https://github.com/ethyca/fidesops/pull/1060)
* Access and erasure support for Logi ID [#1074](https://github.com/ethyca/fidesops/pull/1074)
* Adds infra for email config and dispatch [#1059](https://github.com/ethyca/fidesops/pull/1059)
* Add an endpoint that allows you to create a Saas connector and all supporting resources with a single request [#1076](https://github.com/ethyca/fidesops/pull/1076)
* Add a Connection - SaaS connector's configuration parameters [#761](https://github.com/ethyca/fidesops/pull/1099)
* Saas Connector configuration - left navigation to toggle between connection params and dataset config [#984](https://github.com/ethyca/fidesops/pull/1099)
* SaaS Connector Configuration - Testing a Connection [#985](https://github.com/ethyca/fidesops/pull/1099)
* Add an endpoint for verifying the user's identity before queuing the privacy request. [#1111](https://github.com/ethyca/fidesops/pull/1111)
* Adds tests for email endpoints and service [#1112](https://github.com/ethyca/fidesops/pull/1112)
* Adds the ability to verify a subject's identity before processing a Privacy Request  [#1115](https://github.com/ethyca/fidesops/pull/1115)
* Add option to login as root user from config[#1116](https://github.com/ethyca/fidesops/pull/1116)
* Added email templates [#1123](https://github.com/ethyca/fidesops/pull/1123)
* Add Retry button back into the subject request detail view [#1128](https://github.com/ethyca/fidesops/pull/1131)

### Developer Experience

* When releases are published, dispatch a repository webhook event to ethyca/fidesdemo [#1075](https://github.com/ethyca/fidesops/pull/1075)

### Fixed

* HTTP headers are now preserved in requests generated from SaaS connector pagination [#1069](https://github.com/ethyca/fidesops/pull/1069)
* Bump fideslib to fix issue where the authenticate button in the FastAPI docs did not work [#1092](https://github.com/ethyca/fidesops/pull/1092)
* Escape the Redis user and password to make them URL friendly [#1104](https://github.com/ethyca/fidesops/pull/1104)
* Reduced number of connections opened against app db during health checks [#1107](https://github.com/ethyca/fidesops/pull/1107)
* Fix FIDESOPS__ROOT_USER__ANALYTICS_ID generation when env var is set [#1113](https://github.com/ethyca/fidesops/pull/1113) 
* Set localhost to None for non-endpoint events [#1130](https://github.com/ethyca/fidesops/pull/1130)
* Fixed docs build in CI [#1138](https://github.com/ethyca/fidesops/pull/1138)
* Added future annotations to privacy_request.py for backwards compatibility [#1136](https://github.com/ethyca/fidesops/pull/1136)

### Changed

* Update request status endpoint to return both audit and execution logs [#1068] (https://github.com/ethyca/fidesops/pull/1068/)
* Update backend routing to handle dynamic frontend routes [#1033](https://github.com/ethyca/fidesops/pull/1033)
* Make connection type search case-insensitive [#1133](https://github.com/ethyca/fidesops/pull/1133)
* Adjust log formatting to be %-style instead of f-string [#1132](https://github.com/ethyca/fidesops/pull/1132)

### Docs

* Minor formatting updates to [Policy Webhooks](https://ethyca.github.io/fidesops/guides/policy_webhooks/) documentation [#1114](https://github.com/ethyca/fidesops/pull/1114)

### Removed

* Removed create superuser [#1116](https://github.com/ethyca/fidesops/pull/1116)

## [1.7.0](https://github.com/ethyca/fidesops/compare/1.6.3...1.7.0)

### Added

* Erasure support for Salesforce [#888](https://github.com/ethyca/fidesops/pull/888)
* Publish a `dev` tagged image on every push to main [#956](https://github.com/ethyca/fidesops/pull/956)
* Access and erasure support for Sendgrid contacts endpoint [#883](https://github.com/ethyca/fidesops/pull/883)
* Added saas config base info to connection config responses [#904](https://github.com/ethyca/fidesops/pull/904)
* Access and erasure support for Adobe Campaign [#905](https://github.com/ethyca/fidesops/pull/905)
* Added db vs saas to connection type api [#937](https://github.com/ethyca/fidesops/pull/937)
* Retry a DSR (FE) [#863](https://github.com/ethyca/fidesops/pull/938)
* Add a Connection - Select a connector to configure (front end) [#760](https://github.com/ethyca/fidesops/pull/987)
* Add a Connection - Front End layout structure [#866](https://github.com/ethyca/fidesops/pull/987)
* Enable python function overrides for SaaS connector request execution [#986](https://github.com/ethyca/fidesops/pull/986)
* add Events and logs section to Subject Request Details Page [#1018](https://github.com/ethyca/fidesops/pull/1018)
* Access and erasure support for Auth0 [#991](https://github.com/ethyca/fidesops/pull/991)
* Start better understanding how request execution fails [#993](https://github.com/ethyca/fidesops/pull/993)
* Add approval `AuditLog`s for user and sytem approved privacy requests [#1038](https://github.com/ethyca/fidesops/pull/1038)
* Add finished `AuditLog` for subject requests [#1040](https://github.com/ethyca/fidesops/pull/1040)

### Changed

* Users should be able to click on the full field of a dropdown-type filter to open up the dropdown [#747](https://github.com/ethyca/fidesops/pull/903)
* Reorganize the core code logic to be easier to merge with fidesctl [#1058](https://github.com/ethyca/fidesops/pull/1058)
* Updated the python docker base image from slim-buster to slim-bullseye [#928](https://github.com/ethyca/fidesops/pull/928)
* Removed ipython from the docker install [#928](https://github.com/ethyca/fidesops/pull/928)
* Run static nox checks outside of Docker [#1053](https://github.com/ethyca/fidesops/pull/1053)
* Serve admin UI by default [#906](https://github.com/ethyca/fidesops/pull/936)
* Move tests into an `ops` subdir [#935](https://github.com/ethyca/fidesops/pull/935)
* Move client code into an `ops` subdir [#964](https://github.com/ethyca/fidesops/pull/964)
* Updated the docs docker base image to be consistent with the fidesops image [#949](https://github.com/ethyca/fidesops/pull/949)
* Update fidesops to use bcrypt for hashing [#876](https://github.com/ethyca/fidesops/pull/876)

### Changed

* Updated fideslog==1.1.0 [#890](https://github.com/ethyca/fidesops/pull/890)

### Developer Experience

* Fix randomly failing mssql integration tests [#918](https://github.com/ethyca/fidesops/pull/918)
* Update the way `make clean` works [#767](https://github.com/ethyca/fidesops/pull/767)
* When releases are published, dispatch a repository webhook event to ethyca/fidesops-plus [#945](https://github.com/ethyca/fidesops/pull/945)
* Added `nox` commands to replace the `Makefile` [#919](https://github.com/ethyca/fidesops/pull/919)
* GitHub Actions Workflows leverage `nox` commands [#966](https://github.com/ethyca/fidesops/pull/966)
* The `docker-compose.yml` file no longer handles builds [#966](https://github.com/ethyca/fidesops/pull/966)

### Docs

* Added zendesk and salesforce connection pages [#908](https://github.com/ethyca/fidesops/pull/908)
* Added documentation for OAuth2 configuration and usage [#963](https://github.com/ethyca/fidesops/pull/963)
* Added nox command documentation [#981](https://github.com/ethyca/fidesops/pull/981)
* Updated references to `fidesops.toml` to use lowercase values [#952](https://github.com/ethyca/fidesops/pull/952)

### Fixed

* Correct build arg variable name [#925](https://github.com/ethyca/fidesops/pull/925)
* Reduce number of clients connected to the application db [#944](https://github.com/ethyca/fidesops/pull/944)
* Patch versioneer to allow editable installs [#1070](https://github.com/ethyca/fidesops/pull/1070)
* Add setuptools to dev-requirements to fix versioneer error and revert patch [#1072](https://github.com/ethyca/fidesops/pull/1072)

## [1.6.3](https://github.com/ethyca/fidesops/compare/1.6.2...1.6.3)

### Added

* Adds `COMPOSE_SERVICE_NAME` to `Makefile` [#884](https://github.com/ethyca/fidesops/pull/884)

## [1.6.2](https://github.com/ethyca/fidesops/compare/1.6.1...1.6.2)

### Added

* [Admin UI] Update Subject Request status filter to be a multiselect dropdown [#513](https://github.com/ethyca/fidesops/pull/764)
* Add support for multiple statuses to be selected for filtering subject requests [#660](https://github.com/ethyca/fidesops/pull/802)
* [Datastore Management] Include Icon with datastore connection (FE)[#671](https://github.com/ethyca/fidesops/pull/845)
* Store provided identity data in the privacy request table [#743](https://github.com/ethyca/fidesops/pull/834)
* [Datastore Management] Keep datastore cards in 1/3 screen pattern [#745](https://github.com/ethyca/fidesops/pull/873)
* Adds SaaS connection type to SaaS yaml config [748](https://github.com/ethyca/fidesops/pull/748)
* Adds exact match identity search to the privacy request status endpoint [#765](https://github.com/ethyca/fidesops/pull/847/)
* Adds endpoint to get available connectors (database and saas) [#768](https://github.com/ethyca/fidesops/pull/768)
* Erasure support for Zendesk [#775](https://github.com/ethyca/fidesops/pull/775)
* Adds endpoint to get the secrets required for different connectors [#795](https://github.com/ethyca/fidesops/pull/795)
* Adds Vault for secrets management [#688](https://github.com/ethyca/fidesops/pull/869)
* Adds privacy_request_id placeholder to use in SaaS configs [#911](https://github.com/ethyca/fidesops/pull/911)

### Changed

* Update clipboard icon in Admin UI [#838](https://github.com/ethyca/fidesops/pull/838)
* Stop masking uvicorn logs by default [#831](https://github.com/ethyca/fidesops/pull/831)
* Bump fideslib to handle base64 encoded password [#820](https://github.com/ethyca/fidesops/pull/820)
* Return identity data from application DB, instead of cache [#860](https://github.com/ethyca/fidesops/pull/860)
* Update admin ui to be served from the root route `/` [#720](https://github.com/ethyca/fidesops/pull/720)
* Refactored the root directory and various Docker-related files [#877](https://github.com/ethyca/fidesops/pull/877)

### Developer Experience

* Replace user authentication routes with fideslib routes [#811](https://github.com/ethyca/fidesops/pull/811)
* Reduce docker image size [#846](https://github.com/ethyca/fidesops/pull/846)
* Load Celery config overrides from a dedicated `celery.toml` [#821](https://github.com/ethyca/fidesops/pull/821)

### Docs

* Backend UI deployment [#827](https://github.com/ethyca/fidesops/pull/827)
* Fix publish_docs CI action [#818](https://github.com/ethyca/fidesops/pull/818)
* Reorganize docs and standardize formatting [#858](https://github.com/ethyca/fidesops/pull/858)
* Changed wording on Admin UI login page [#774](https://github.com/ethyca/fidesops/pull/774)
* Fixed typos in Admin UI [#774](https://github.com/ethyca/fidesops/pull/774)

### Fixed

* Resolve issue with MyPy seeing files in fidesops as missing imports [#719](https://github.com/ethyca/fidesops/pull/719)
* Fixed `check-migrations` Make command [#806](https://github.com/ethyca/fidesops/pull/806)
* Fix issue requiring separate install of snowflake-connector-python [#807](https://github.com/ethyca/fidesops/pull/807)
* [User Management] Create new user gives HTTP 422 Unprocessable Entity exception [#833](https://github.com/ethyca/fidesops/pull/833)
* Fix error when running `make test-data` [862](https://github.com/ethyca/fidesops/pull/862)
* [User Management] Refactored New and Edit user pages to reduce duplicate code [#839](https://github.com/ethyca/fidesops/pull/839)
* Fix error when there are no scopes in `ClientDetail` [#830](https://github.com/ethyca/fidesops/pull/830)

## [1.6.1](https://github.com/ethyca/fidesops/compare/1.6.0...1.6.1)

### Added

* `fidesops worker` command for running a Celery worker [#673](https://github.com/ethyca/fidesops/pull/673/)

### Developer Experience

* Add fixture to clear tables between test [#680](https://github.com/ethyca/fidesops/pull/680)
* Reduce the size of the docker image [#707](https://github.com/ethyca/fidesops/pull/707)
* Parallelize CI safe checks to reduce run time [#717](https://github.com/ethyca/fidesops/pull/717)
* Add dependabot to keep dependencies up to date [#718](https://github.com/ethyca/fidesops/pull/718)
* Make running a worker node optional [#770](https://github.com/ethyca/fidesops/pull/770)

### Changed

* Base64 encode passwords on frontend [#749](https://github.com/ethyca/fidesops/pull/749)

### Docs

* Updated the tutorial installation to use main in fidesdemo [#715](https://github.com/ethyca/fidesops/pull/715)
* Added a page on how to use the datastore UI [#742](https://github.com/ethyca/fidesops/pull/742)
* Added a page on implementing and opting out of fideslog analytics [#751](https://github.com/ethyca/fidesops/pull/751)

### Fixed

* Make reading of environment variables case insensitive [#712](https://github.com/ethyca/fidesops/pull/712)
* Fix console warning in disable connection modal [#750](https://github.com/ethyca/fidesops/pull/750)
* Fix no such container error with docker-compose [#758](https://github.com/ethyca/fidesops/pull/758)
* Fixed issue with extending the configuration [#721](https://github.com/ethyca/fidesops/pull/721)

## [1.6.0](https://github.com/ethyca/fidesops/compare/1.5.3...1.6.0)

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
* Sample dataset for Salesforce with access configuration [#676](https://github.com/ethyca/fidesops/pull/676)
* Sample dataset and access configuration for Zendesk (ticket endpoints) [#677](https://github.com/ethyca/fidesops/pull/677)
* Include number of records to be masked in masking endpoint's log message [#692](https://github.com/ethyca/fidesops/pull/692)
* Datastore Connection Landing Page [#674](https://github.com/ethyca/fidesops/pull/674)
* Added the ability to delete a datastore from the frontend [#683](https://github.com/ethyca/fidesops/pull/683)
* Added the ability to disable/enable a datastore from the frontend [#693](https://github.com/ethyca/fidesops/pull/693)
* Adds Postgres and Redis health checks to health endpoint [#690](https://github.com/ethyca/fidesops/pull/690)
* Adds the ability to revoke a pending privacy request [#592](https://github.com/ethyca/fidesops/pull/592/files)
* Added health checks and better error messages on app startup for both db and cache [#686](https://github.com/ethyca/fidesops/pull/686)
* Datastore Connection Filters [#691](https://github.com/ethyca/fidesops/pull/691)

### Changed

* Refactor auth and enable static file serving [#577](https://github.com/ethyca/fidesops/pull/577)
* Bumped mypy to version 0.961 [#630](https://github.com/ethyca/fidesops/pull/630)
* Bumped Python to version 3.9.13 in the `Dockerfile` [#630](https://github.com/ethyca/fidesops/pull/630)
* Matched the path to the migrations in the mypy settings with the new location [#634](https://github.com/ethyca/fidesops/pull/634)
* Sort ConnectionConfig by name ascending [#668](https://github.com/ethyca/fidesops/pull/672)
* Install MSSQL By Default [#664](https://github.com/ethyca/fidesops/pull/664)
* [Admin UI] Change "Policy Name" to "Request Type" on SR list page.[#546](https://github.com/ethyca/fidesops/pull/696)
* Queue PrivacyRequests into a Celery queue for execution [#621](https://github.com/ethyca/fidesops/pull/621)
* Added filtering clearing in datastore connections [#701](https://github.com/ethyca/fidesops/pull/701)

### Developer Experience

* Add celerybeat-schedule file to gitignore [#639](https://github.com/ethyca/fidesops/pull/639)
* Use `v2.1.0` of `fideslib` [#705](https://github.com/ethyca/fidesops/pull/705)

### Docs

* Subject Request detail documentation for the UI [#702](https://github.com/ethyca/fidesops/pull/702)

### Fixed

* Fixed error with running mypy on M1 Macs [#630](https://github.com/ethyca/fidesops/pull/630)
* Fixed error with mypy on Python versions greater than 3.9.6 [#630](https://github.com/ethyca/fidesops/pull/630)
* Bumped fideslib to 2.0.4. This fixes the issue where alembic couldn't find the `fidesops.toml` file from its new location [#643](https://github.com/ethyca/fidesops/pull/643)
* Fixes Postman Collection inconsistencies [#704](https://github.com/ethyca/fidesops/pull/704)

## [1.5.3](https://github.com/ethyca/fidesops/compare/1.5.2...1.5.3)

### Changed

* Database migrations now exist as part of the core `fidesops` package [#620](https://github.com/ethyca/fidesops/pull/620)

### Removed

* The `[package]` config section no longer exists [#620](https://github.com/ethyca/fidesops/pull/620)

### Changed

* Process privacy requests as Celery tasks and not background processes [#621](https://github.com/ethyca/fidesops/pull/621)

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

* Update masking API to take multiple input values [#443](https://github.com/ethyca/fidesops/pull/443)

### Docs

* DRP feature documentation [#520](https://github.com/ethyca/fidesops/pull/520)

## [1.4.2](https://github.com/ethyca/fidesops/compare/1.4.1...1.4.2) - 2022-05-12

### Added

* GET routes for users [#405](https://github.com/ethyca/fidesops/pull/405)
* Username based search on GET route [#444](https://github.com/ethyca/fidesops/pull/444)
* FIDESOPS__DEV_MODE for Easier SaaS Request Debugging [#363](https://github.com/ethyca/fidesops/pull/363)
* Track user privileges across sessions [#425](https://github.com/ethyca/fidesops/pull/425)
* Add first_name and last_name fields. Also add them along with created_at to FidesUser response [#465](https://github.com/ethyca/fidesops/pull/465)
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

* Update masking API to take multiple input values [#443](https://github.com/ethyca/fidesops/pull/443)

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
