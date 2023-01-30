
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

## [Unreleased](https://github.com/ethyca/fides/compare/2.5.0...main)


### Added

* Unified Fides Resources: Added a dataset dropdown selector when configuring a connector to link an existing dataset to the connector configuration. [#2162](https://github.com/ethyca/fides/pull/2162)
* Unified Fides Resources: Added new datasetconfig.ctl_dataset_id field to unify fides dataset resources [#2046](https://github.com/ethyca/fides/pull/2046)
* Add new connection config routes that couple them with systems [#2249](https://github.com/ethyca/fides/pull/2249)

### Changed

* Unified Fides Resources: Removed several fidesops schemas for DSR's in favor of updated Fideslang schemas [#2009](https://github.com/ethyca/fides/pull/2009)
* Unified Fides Resources: Removed DatasetConfig.dataset field [#2096](https://github.com/ethyca/fides/pull/2096)
* Unified Fides Resources: Updated UI dataset config routes to use new unified routes [#2113](https://github.com/ethyca/fides/pull/2113)
* Unified Fides Resources: Validate request body on crud endpoints on upsert. Validate dataset data categories before save. [#2134](https://github.com/ethyca/fides/pull/2134/)
* Unified Fides Resources: Updated test env setup and quickstart to use new endpoints [#2225](https://github.com/ethyca/fides/pull/2225)
* Update fideslang to 1.3.3 [#2343](https://github.com/ethyca/fides/pull/2343)
* Display the request type instead of the policy name on the request table [#2382](https://github.com/ethyca/fides/pull/2382)
* Make denial reasons required [#2400](https://github.com/ethyca/fides/pull/2400)
* Display the policy key on the request details page [#2395](https://github.com/ethyca/fides/pull/2395)

### Developer Experience

* `nox -s test_env` now uses a production fides image so the built UI can be accessed at `localhost:8080` [#2399](https://github.com/ethyca/fides/pull/2399)
* `nox -s dev_env` replaces the functionality of the former `nox -s test_env` and still uses a dev fides image so hot reloading can work [#2399](https://github.com/ethyca/fides/pull/2399)
* Change from code climate to codecov for coverage reporting [#2402](https://github.com/ethyca/fides/pull/2402)

### Fixed

* Home screen header scaling and responsiveness issues [#2200](https://github.com/ethyca/fides/pull/2277)
* Added a feature flag for the recent dataset classification UX changes [#2335](https://github.com/ethyca/fides/pull/2335)
* Privacy Center identity inputs validate even when they are optional. [#2308](https://github.com/ethyca/fides/pull/2308)
* Patch masking strategies to better handle null and non-string inputs [#2307](https://github.com/ethyca/fides/pull/2377)

### Security

* Add a check to the catchall path to prevent returning paths outside of the UI directory [#2330](https://github.com/ethyca/fides/pull/2330)

### Developer Experience

* Reduce size of local Docker images by fixing `.dockerignore` patterns [#2360](https://github.com/ethyca/fides/pull/2360)

## [2.5.0](https://github.com/ethyca/fides/compare/2.4.0...2.5.0)

### Docs

* Update the docs landing page and remove redundant docs [#2184](https://github.com/ethyca/fides/pull/2184)

### Added

* Added the `user` command group to the CLI. [#2153](https://github.com/ethyca/fides/pull/2153)
* Added `Code Climate` test coverage uploads.  [#2198](https://github.com/ethyca/fides/pull/2198)
* Added the connection key to the execution log [#2100](https://github.com/ethyca/fides/pull/2100)
* Added endpoints to retrieve DSR `Rule`s and `Rule Target`s [#2116](https://github.com/ethyca/fides/pull/2116)
* Added Fides version number to account dropdown in the UI [#2140](https://github.com/ethyca/fides/pull/2140)
* Add link to Classify Systems page in nav side bar [#2128](https://github.com/ethyca/fides/pull/2128)
* Dataset classification UI now polls for results [#2123](https://github.com/ethyca/fides/pull/2123)
* Update Privacy Center Icons [#1800](https://github.com/ethyca/fides/pull/2139)
* Privacy Center `fides-consent.js`:
  * `Fides.shopify` integration function. [#2152](https://github.com/ethyca/fides/pull/2152)
  * Dedicated folder for integrations.
  * `Fides.meta` integration function (fbq). [#2217](https://github.com/ethyca/fides/pull/2217)
* Adds support for Twilio email service (Sendgrid) [#2154](https://github.com/ethyca/fides/pull/2154)
* Access and erasure support for Recharge [#1709](https://github.com/ethyca/fides/pull/1709)
* Access and erasure support for Friendbuy Nextgen [#2085](https://github.com/ethyca/fides/pull/2085)

### Changed

* Admin UI Feature Flags - [#2101](https://github.com/ethyca/fides/pull/2101)
  * Overrides can be saved in the browser.
  * Use `NEXT_PUBLIC_APP_ENV` for app-specific environment config.
  * No longer use `react-feature-flags` library.
  * Can have descriptions. [#2243](https://github.com/ethyca/fides/pull/2243)
* Made privacy declarations optional when adding systems manually - [#2173](https://github.com/ethyca/fides/pull/2173)
* Removed an unclear logging message. [#2266](https://github.com/ethyca/fides/pull/2266)
* Allow any user with `user:delete` scope to delete other users [#2148](https://github.com/ethyca/fides/pull/2148)
* Dynamic imports of custom overrides and SaaS test fixtures [#2169](https://github.com/ethyca/fides/pull/2169)
* Added `AuthenticatedClient` to custom request override interface [#2171](https://github.com/ethyca/fides/pull/2171)
* Only approve the specific collection instead of the entire dataset, display only top 1 classification by default [#2226](https://github.com/ethyca/fides/pull/2226)
* Update sample project resources for `fides evaluate` usage in `fides deploy` [#2253](https://github.com/ethyca/fides/pull/2253)

### Removed

* Removed unused object_name field on s3 storage config [#2133](https://github.com/ethyca/fides/pull/2133)

### Fixed

* Remove next-auth from privacy center to fix JS console error [#2090](https://github.com/ethyca/fides/pull/2090)
* Admin UI - Added Missing ability to assign `user:delete` in the permissions checkboxes [#2148](https://github.com/ethyca/fides/pull/2148)
* Nav bug: clicking on Privacy Request breadcrumb takes me to Home instead of /privacy-requests [#497](https://github.com/ethyca/fides/pull/2141)
* Side nav disappears when viewing request details [#2129](https://github.com/ethyca/fides/pull/2155)
* Remove usage of load dataset button and other dataset UI modifications [#2149](https://github.com/ethyca/fides/pull/2149)
* Improve readability for exceptions raised from custom request overrides [#2157](https://github.com/ethyca/fides/pull/2157)
* Importing custom request overrides on server startup [#2186](https://github.com/ethyca/fides/pull/2186)
* Remove warning when env vars default to blank strings in docker-compose [#2188](https://github.com/ethyca/fides/pull/2188)
* Fix Cookie House purchase modal flashing 'Error' in title [#2274](https://github.com/ethyca/fides/pull/2274)
* Stop dependency from upgrading `packaging` to version with known issue [#2273](https://github.com/ethyca/fides/pull/2273)
* Privacy center config no longer requires `identity_inputs` and will use `email` as a default [#2263](https://github.com/ethyca/fides/pull/2263)
* No longer display remaining days for privacy requests in terminal states [#2292](https://github.com/ethyca/fides/pull/2292)

### Removed

* Remove "Create New System" button when viewing systems. All systems can now be created via the "Add systems" button on the home page. [#2132](https://github.com/ethyca/fides/pull/2132)


## [2.4.0](https://github.com/ethyca/fides/compare/2.3.1...2.4.0)

### Developer Experience

* Include a pre-check workflow that collects the pytest suite [#2098](https://github.com/ethyca/fides/pull/2098)
* Write to the application db when running the app locally. Write to the test db when running pytest [#1731](https://github.com/ethyca/fides/pull/1731)

### Changed

* Move the `fides.ctl.core.` and `fides.ctl.connectors` modules into `fides.core` and `fides.connectors` respectively [#2097](https://github.com/ethyca/fides/pull/2097)
* Fides: Skip cypress tests due to nav bar 2.0 [#2102](https://github.com/ethyca/fides/pull/2103)

### Added

* Adds new erasure policy for complete user data masking [#1839](https://github.com/ethyca/fides/pull/1839)
* New Fides Home page [#1864](https://github.com/ethyca/fides/pull/2050)
* Nav 2.0 - Replace form flow side navs with top tabs [#2037](https://github.com/ethyca/fides/pull/2050)
* Adds new erasure policy for complete user data masking [#1839](https://github.com/ethyca/fides/pull/1839)
* Added ability to use Mailgun templates when sending emails. [#2039](https://github.com/ethyca/fides/pull/2039)
* Adds SMS id verification for consent [#2094](https://github.com/ethyca/fides/pull/2094)

### Fixed

* Store `fides_consent` cookie on the root domain of the Privacy Center [#2071](https://github.com/ethyca/fides/pull/2071)
* Properly set the expire-time for verification codes [#2105](https://github.com/ethyca/fides/pull/2105)

## [2.3.1](https://github.com/ethyca/fides/compare/2.3.0...2.3.1)

### Fixed

* Resolved an issue where the root_user was not being created [#2082](https://github.com/ethyca/fides/pull/2082)

### Added

* Nav redesign with sidebar groups. Feature flagged to only be visible in dev mode until release. [#2030](https://github.com/ethyca/fides/pull/2047)
* Improved error handling for incorrect app encryption key [#2089](https://github.com/ethyca/fides/pull/2089)
* Access and erasure support for Friendbuy API [#2019](https://github.com/ethyca/fides/pull/2019)

## [2.3.0](https://github.com/ethyca/fides/compare/2.2.2...2.3.0)

### Added

* Common Subscriptions for app-wide data and feature checks. [#2030](https://github.com/ethyca/fides/pull/2030)
* Send email alerts on privacy request failures once the specified threshold is reached. [#1793](https://github.com/ethyca/fides/pull/1793)
* DSR Notifications (toast) [#1895](https://github.com/ethyca/fides/pull/1895)
* DSR configure alerts btn [#1895](https://github.com/ethyca/fides/pull/1895)
* DSR configure alters (FE) [#1895](https://github.com/ethyca/fides/pull/1895)
* Add a `usage` session to Nox to print full session docstrings. [#2022](https://github.com/ethyca/fides/pull/2022)

### Added

* Adds notifications section to toml files [#2026](https://github.com/ethyca/fides/pull/2060)

### Changed

* Updated to use `loguru` logging library throughout codebase [#2031](https://github.com/ethyca/fides/pull/2031)
* Do not always create a `fides.toml` by default [#2023](https://github.com/ethyca/fides/pull/2023)
* The `fideslib` module has been merged into `fides`, code redundancies have been removed [#1859](https://github.com/ethyca/fides/pull/1859)
* Replace 'ingress' and 'egress' with 'sources' and 'destinations' across UI [#2044](https://github.com/ethyca/fides/pull/2044)
* Update the functionality of `fides pull -a <filename>` to include _all_ resource types. [#2083](https://github.com/ethyca/fides/pull/2083)

### Fixed

* Timing issues with bulk DSR reprocessing, specifically when analytics are enabled [#2015](https://github.com/ethyca/fides/pull/2015)
* Error caused by running erasure requests with disabled connectors [#2045](https://github.com/ethyca/fides/pull/2045)
* Changes the SlowAPI ratelimiter's backend to use memory instead of Redis [#2054](https://github.com/ethyca/fides/pull/2058)

## [2.2.2](https://github.com/ethyca/fides/compare/2.2.1...2.2.2)

### Docs

* Updated the readme to use new new [docs site](http://docs.ethyca.com) [#2020](https://github.com/ethyca/fides/pull/2020)

### Deprecated

* The documentation site hosted in the `/docs` directory has been deprecated. All documentation updates will be hosted at the new [docs site](http://docs.ethyca.com) [#2020](https://github.com/ethyca/fides/pull/2020)

### Fixed

* Fixed mypy and pylint errors [#2013](https://github.com/ethyca/fides/pull/2013)
* Update connection test endpoint to be effectively non-blocking [#2000](https://github.com/ethyca/fides/pull/2000)
* Update Fides connector to better handle children with no access results [#2012](https://github.com/ethyca/fides/pull/2012)

## [2.2.1](https://github.com/ethyca/fides/compare/2.2.0...2.2.1)

### Added

* Add health check indicator for data flow scanning option [#1973](https://github.com/ethyca/fides/pull/1973)

### Changed

* The `celery.toml` is no longer used, instead it is a subsection of the `fides.toml` file [#1990](https://github.com/ethyca/fides/pull/1990)
* Update sample project landing page copy to be version-agnostic [#1958](https://github.com/ethyca/fides/pull/1958)
* `get` and `ls` CLI commands now return valid `fides` object YAML [#1991](https://github.com/ethyca/fides/pull/1991)

### Developer Experience

* Remove duplicate fastapi-caching and pin version. [#1765](https://github.com/ethyca/fides/pull/1765)

## [2.2.0](https://github.com/ethyca/fides/compare/2.1.0...2.2.0)

### Added

* Send email alerts on privacy request failures once the specified threshold is reached. [#1793](https://github.com/ethyca/fides/pull/1793)
* Add authenticated privacy request route. [#1819](https://github.com/ethyca/fides/pull/1819)
* Enable the onboarding flow [#1836](https://github.com/ethyca/fides/pull/1836)
* Access and erasure support for Fullstory API [#1821](https://github.com/ethyca/fides/pull/1821)
* Add function to poll privacy request for completion [#1860](https://github.com/ethyca/fides/pull/1860)
* Added rescan flow for the data flow scanner [#1844](https://github.com/ethyca/fides/pull/1844)
* Add rescan flow for the data flow scanner [#1844](https://github.com/ethyca/fides/pull/1844)
* Add Fides connector to support parent-child Fides deployments [#1861](https://github.com/ethyca/fides/pull/1861)
* Classification UI now polls for updates to classifications [#1908](https://github.com/ethyca/fides/pull/1908)

### Changed

* The organization info form step is now skipped if the server already has organization info. [#1840](https://github.com/ethyca/fides/pull/1840)
* Removed the description column from the classify systems page. [#1867](https://github.com/ethyca/fides/pull/1867)
* Retrieve child results during fides connector execution [#1967](https://github.com/ethyca/fides/pull/1967)

### Fixed

* Fix error in parent user creation seeding. [#1832](https://github.com/ethyca/fides/issues/1832)
* Fix DSR error due to unfiltered empty identities [#1901](https://github.com/ethyca/fides/pull/1907)

### Docs

* Remove documentation about no-longer used connection string override [#1824](https://github.com/ethyca/fides/pull/1824)
* Fix typo in headings [#1824](https://github.com/ethyca/fides/pull/1824)
* Update documentation to reflect configs necessary for mailgun, twilio_sms and twilio_email service types [#1846](https://github.com/ethyca/fides/pull/1846)

...

## [2.1.0](https://github.com/ethyca/fides/compare/2.0.0...2.1.0)

### Added

* Classification flow for system data flows
* Classification is now triggered as part of data flow scanning
* Include `ingress` and `egress` fields on system export and `datamap/` endpoint [#1740](https://github.com/ethyca/fides/pull/1740)
* Repeatable unique identifier for dataset fides_keys and metadata [#1786](https://github.com/ethyca/fides/pull/1786)
* Adds SMS support for identity verification notifications [#1726](https://github.com/ethyca/fides/pull/1726)
* Added phone number validation in back-end and react phone number form in Privacy Center [#1745](https://github.com/ethyca/fides/pull/1745)
* Adds SMS message template for all subject notifications [#1743](https://github.com/ethyca/fides/pull/1743)
* Privacy-Center-Cypress workflow for CI checks of the Privacy Center. [#1722](https://github.com/ethyca/fides/pull/1722)
* Privacy Center `fides-consent.js` script for accessing consent on external pages. [Details](/clients/privacy-center/packages/fides-consent/README.md)
* Erasure support for Twilio Conversations API [#1673](https://github.com/ethyca/fides/pull/1673)
* Webserver port can now be configured via the CLI command [#1858](https://github.com/ethyca/fides/pull/1858)

### Changed

* Optional dependencies are no longer used for 3rd-party connectivity. Instead they are used to isolate dangerous dependencies. [#1679](https://github.com/ethyca/fides/pull/1679)
* All Next pages now automatically require login. [#1670](https://github.com/ethyca/fides/pull/1670)
* Running the `webserver` command no longer prompts the user to opt out/in to analytics[#1724](https://github.com/ethyca/fides/pull/1724)

### Developer Experience

* Admin-UI-Cypress tests that fail in CI will now upload screen recordings for debugging. [#1728](https://github.com/ethyca/fides/pull/1728/files/c23e62fea284f7910028c8483feff893903068b8#r1019491323)
* Enable remote debugging from VSCode of live dev app [#1780](https://github.com/ethyca/fides/pull/1780)

### Removed

* Removed the Privacy Center `cookieName` config introduced in 2.0.0. [#1756](https://github.com/ethyca/fides/pull/1756)

### Fixed

* Exceptions are no longer raised when sending analytics on Windows [#1666](https://github.com/ethyca/fides/pull/1666)
* Fixed wording on identity verification modal in the Privacy Center [#1674](https://github.com/ethyca/fides/pull/1674)
* Update system fides_key tooltip text [#1533](https://github.com/ethyca/fides/pull/1685)
* Removed local storage parsing that is redundant with redux-persist. [#1678](https://github.com/ethyca/fides/pull/1678)
* Show a helpful error message if Docker daemon is not running during "fides deploy" [#1694](https://github.com/ethyca/fides/pull/1694)
* Allow users to query their own permissions, including root user. [#1698](https://github.com/ethyca/fides/pull/1698)
* Single-select taxonomy fields legal basis and special category can be cleared. [#1712](https://github.com/ethyca/fides/pull/1712)
* Fixes the issue where the security config is not properly loading from environment variables. [#1718](https://github.com/ethyca/fides/pull/1718)
* Fixes the issue where the CLI can't run without the config values required by the webserver. [#1811](https://github.com/ethyca/fides/pull/1811)
* Correctly handle response from adobe jwt auth endpoint as milliseconds, rather than seconds. [#1754](https://github.com/ethyca/fides/pull/1754)
* Fixed styling issues with the `EditDrawer` component. [#1803](https://github.com/ethyca/fides/pull/1803)

### Security

* Bumped versions of packages that use OpenSSL [#1683](https://github.com/ethyca/fides/pull/1683)

## [2.0.0](https://github.com/ethyca/fides/compare/1.9.6...2.0.0)

### Added

* Allow delete-only SaaS connector endpoints [#1200](https://github.com/ethyca/fides/pull/1200)
* Privacy center consent choices store a browser cookie. [#1364](https://github.com/ethyca/fides/pull/1364)
  * The format is generic. A reasonable set of defaults will be added later: [#1444](https://github.com/ethyca/fides/issues/1444)
  * The cookie name defaults to `fides_consent` but can be configured under `config.json > consent > cookieName`.
  * Each consent option can provide an array of `cookieKeys`.
* Individually select and reprocess DSRs that have errored [#1203](https://github.com/ethyca/fides/pull/1489)
* Bulk select and reprocess DSRs that have errored [#1205](https://github.com/ethyca/fides/pull/1489)
* Config Wizard: AWS scan results populate in system review forms. [#1454](https://github.com/ethyca/fides/pull/1454)
* Integrate rate limiter with Saas Connectors. [#1433](https://github.com/ethyca/fides/pull/1433)
* Config Wizard: Added a column selector to the scan results page of the config wizard [#1590](https://github.com/ethyca/fides/pull/1590)
* Config Wizard: Flow for runtime scanner option [#1640](https://github.com/ethyca/fides/pull/1640)
* Access support for Twilio Conversations API [#1520](https://github.com/ethyca/fides/pull/1520)
* Message Config: Adds Twilio Email/SMS support [#1519](https://github.com/ethyca/fides/pull/1519)

### Changed

* Updated mypy to version 0.981 and Python to version 3.10.7 [#1448](https://github.com/ethyca/fides/pull/1448)

### Developer Experience

* Repository dispatch events are sent to fidesctl-plus and fidesops-plus [#1263](https://github.com/ethyca/fides/pull/1263)
* Only the `docs-authors` team members are specified as `CODEOWNERS` [#1446](https://github.com/ethyca/fides/pull/1446)
* Updates the default local configuration to not defer tasks to a worker node [#1552](https://github.com/ethyca/fides/pull/1552/)
* Updates the healthcheck to return health status of connected Celery workers [#1588](https://github.com/ethyca/fides/pull/1588)

### Docs

* Remove the tutorial to prepare for new update [#1543](https://github.com/ethyca/fides/pull/1543)
* Add system management via UI documentation [#1541](https://github.com/ethyca/fides/pull/1541)
* Added DSR quickstart docs, restructured docs navigation [#1651](https://github.com/ethyca/fides/pull/1651)
* Update privacy request execution overview docs [#1258](https://github.com/ethyca/fides/pull/1490)

### Fixed

* Fixed system dependencies appearing as "N/A" in the datamap endpoint when there are no privacy declarations [#1649](https://github.com/ethyca/fides/pull/1649)

## [1.9.6](https://github.com/ethyca/fides/compare/1.9.5...1.9.6)

### Fixed

* Include systems without a privacy declaration on data map [#1603](https://github.com/ethyca/fides/pull/1603)
* Handle malformed tokens [#1523](https://github.com/ethyca/fides/pull/1523)
* Remove thrown exception from getAllPrivacyRequests method [#1592](https://github.com/ethyca/fides/pull/1593)
* Include systems without a privacy declaration on data map [#1603](https://github.com/ethyca/fides/pull/1603)
* After editing a dataset, the table will stay on the previously selected collection instead of resetting to the first one. [#1511](https://github.com/ethyca/fides/pull/1511)
* Fix redis `db_index` config issue [#1647](https://github.com/ethyca/fides/pull/1647)

### Docs

* Add unlinked docs and fix any remaining broken links [#1266](https://github.com/ethyca/fides/pull/1266)
* Update privacy center docs to include consent information [#1537](https://github.com/ethyca/fides/pull/1537)
* Update UI docs to include DSR countdown information and additional descriptions/filtering [#1545](https://github.com/ethyca/fides/pull/1545)

### Changed

* Allow multiple masking strategies to be specified when using fides as a masking engine [#1647](https://github.com/ethyca/fides/pull/1647)

## [1.9.5](https://github.com/ethyca/fides/compare/1.9.4...1.9.5)

### Added

* The database includes a `plus_system_scans` relation, to track the status and results of System Scanner executions in fidesctl-plus [#1554](https://github.com/ethyca/fides/pull/1554)

## [1.9.4](https://github.com/ethyca/fides/compare/1.9.2...1.9.4)

### Fixed

* After editing a dataset, the table will stay on the previously selected collection instead of resetting to the first one. [#1511](https://github.com/ethyca/fides/pull/1511)

## [1.9.2](https://github.com/ethyca/fides/compare/1.9.1...1.9.2)

### Deprecated

* Added a deprecation warning for the entire package [#1244](https://github.com/ethyca/fides/pull/1244)

### Added

* Dataset generation enhancements using Fides Classify for Plus users:
  * Integrate Fides Plus API into placeholder features introduced in 1.9.0. [#1194](https://github.com/ethyca/fides/pull/1194)

* Fides Admin UI:
  * Configure Connector after creation [#1204](https://github.com/ethyca/fides/pull/1356)

### Fixed

* Privacy Center:
  * Handle error on startup if server isn't running [#1239](https://github.com/ethyca/fides/pull/1239)
  * Fix styling issue with cards [#1240](https://github.com/ethyca/fides/pull/1240)
  * Redirect to index on consent save [#1238](https://github.com/ethyca/fides/pull/1238)

## [1.9.1](https://github.com/ethyca/fides/compare/1.9.0...1.9.1)

### Changed

* Update fideslang to v1.3.1 [#1136](https://github.com/ethyca/fides/pull/1136)

### Changed

* Update fideslang to v1.3.1 [#1136](https://github.com/ethyca/fides/pull/1136)

## [1.9.0](https://github.com/ethyca/fides/compare/1.8.6...1.9.0) - 2022-09-29

### Added

* Dataset generation enhancements using Fides Classify for Plus users:
  * Added toggle for enabling classify during generation. [#1057](https://github.com/ethyca/fides/pull/1057)
  * Initial implementation of API request to kick off classify, with confirmation modal. [#1069](https://github.com/ethyca/fides/pull/1069)
  * Initial Classification & Review status for generated datasets. [#1074](https://github.com/ethyca/fides/pull/1074)
  * Component for choosing data categories based on classification results. [#1110](https://github.com/ethyca/fides/pull/1110)
  * The dataset fields table shows data categories from the classifier (if available). [#1088](https://github.com/ethyca/fides/pull/1088)
  * The "Approve" button can be used to update the dataset with the classifier's suggestions. [#1129](https://github.com/ethyca/fides/pull/1129)
* System management UI:
  * New page to add a system via yaml [#1062](https://github.com/ethyca/fides/pull/1062)
  * Skeleton of page to add a system manually [#1068](https://github.com/ethyca/fides/pull/1068)
  * Refactor config wizard system forms to be reused for system management [#1072](https://github.com/ethyca/fides/pull/1072)
  * Add additional optional fields to system management forms [#1082](https://github.com/ethyca/fides/pull/1082)
  * Delete a system through the UI [#1085](https://github.com/ethyca/fides/pull/1085)
  * Edit a system through the UI [#1096](https://github.com/ethyca/fides/pull/1096)
* Cypress component testing [#1106](https://github.com/ethyca/fides/pull/1106)

### Changed

* Changed behavior of `load_default_taxonomy` to append instead of upsert [#1040](https://github.com/ethyca/fides/pull/1040)
* Changed behavior of adding privacy declarations to decouple the actions of the "add" and "next" buttons [#1086](https://github.com/ethyca/fides/pull/1086)
* Moved system related UI components from the `config-wizard` directory to the `system` directory [#1097](https://github.com/ethyca/fides/pull/1097)
* Updated "type" on SaaS config to be a simple string type, not an enum [#1197](https://github.com/ethyca/fides/pull/1197)

### Developer Experience

* Optional dependencies may have their version defined only once, in `optional-requirements.txt` [#1171](https://github.com/ethyca/fides/pull/1171)

### Docs

* Updated the footer links [#1130](https://github.com/ethyca/fides/pull/1130)

### Fixed

* Fixed the "help" link in the UI header [#1078](https://github.com/ethyca/fides/pull/1078)
* Fixed a bug in Data Category Dropdowns where checking i.e. `user.biometric` would also check `user.biometric_health` [#1126](https://github.com/ethyca/fides/pull/1126)

### Security

* Upgraded pymysql to version `1.0.2` [#1094](https://github.com/ethyca/fides/pull/1094)

## [1.8.6](https://github.com/ethyca/fides/compare/1.8.5...1.8.6) - 2022-09-28

### Added

* Added classification tables for Plus users [#1060](https://github.com/ethyca/fides/pull/1060)

### Fixed

* Fixed a bug where rows were being excluded from a data map [#1124](https://github.com/ethyca/fides/pull/1124)

## [1.8.5](https://github.com/ethyca/fides/compare/1.8.4...1.8.5) - 2022-09-21

### Changed

* Update fideslang to v1.3.0 [#1103](https://github.com/ethyca/fides/pull/1103)

## [1.8.4](https://github.com/ethyca/fides/compare/1.8.3...1.8.4) - 2022-09-09

### Added

* Initial system management page [#1054](https://github.com/ethyca/fides/pull/1054)

### Changed

* Deleting a taxonomy field with children will now cascade delete all of its children as well. [#1042](https://github.com/ethyca/fides/pull/1042)

### Fixed

* Fixed navigating directly to frontend routes loading index page instead of the correct static page for the route.
* Fix truncated evaluation error messages [#1053](https://github.com/ethyca/fides/pull/1053)

## [1.8.3](https://github.com/ethyca/fides/compare/1.8.2...1.8.3) - 2022-09-06

### Added

* Added more taxonomy fields that can be edited via the UI [#1000](https://github.com/ethyca/fides/pull/1000) [#1028](https://github.com/ethyca/fides/pull/1028)
* Added the ability to add taxonomy fields via the UI [#1019](https://github.com/ethyca/fides/pull/1019)
* Added the ability to delete taxonomy fields via the UI [#1006](https://github.com/ethyca/fides/pull/1006)
  * Only non-default taxonomy entities can be deleted [#1023](https://github.com/ethyca/fides/pull/1023)
* Prevent deleting taxonomy `is_default` fields and from adding `is_default=True` fields via the API [#990](https://github.com/ethyca/fides/pull/990).
* Added a "Custom" tag to distinguish user defined taxonomy fields from default taxonomy fields in the UI [#1027](https://github.com/ethyca/fides/pull/1027)
* Added initial support for enabling Fides Plus [#1037](https://github.com/ethyca/fides/pull/1037)
  * The `useFeatures` hook can be used to check if `plus` is enabled.
  * Navigating to/from the Data Map page is gated behind this feature.
  * Plus endpoints are served from the private Plus image.

### Fixed

* Fixed failing mypy tests [#1030](https://github.com/ethyca/fides/pull/1030)
* Fixed an issue where `fides push --diff` would return a false positive diff [#1026](https://github.com/ethyca/fides/pull/1026)
* Pinned pydantic version to < 1.10.0 to fix an error in finding referenced fides keys [#1045](https://github.com/ethyca/fides/pull/1045)

### Fixed

* Fixed failing mypy tests [#1030](https://github.com/ethyca/fides/pull/1030)
* Fixed an issue where `fides push --diff` would return a false positive diff [#1026](https://github.com/ethyca/fides/pull/1026)

### Docs

* Minor formatting updates to [Policy Webhooks](https://ethyca.github.io/fidesops/guides/policy_webhooks/) documentation [#1114](https://github.com/ethyca/fidesops/pull/1114)

### Removed

* Removed create superuser [#1116](https://github.com/ethyca/fidesops/pull/1116)

## [1.8.2](https://github.com/ethyca/fides/compare/1.8.1...1.8.2) - 2022-08-18

### Added

* Added the ability to edit taxonomy fields via the UI [#977](https://github.com/ethyca/fides/pull/977) [#1028](https://github.com/ethyca/fides/pull/1028)
* New column `is_default` added to DataCategory, DataUse, DataSubject, and DataQualifier tables [#976](https://github.com/ethyca/fides/pull/976)
* Added the ability to add taxonomy fields via the UI [#1019](https://github.com/ethyca/fides/pull/1019)
* Added the ability to delete taxonomy fields via the UI [#1006](https://github.com/ethyca/fides/pull/1006)
  * Only non-default taxonomy entities can be deleted [#1023](https://github.com/ethyca/fides/pull/1023)
* Prevent deleting taxonomy `is_default` fields and from adding `is_default=True` fields via the API [#990](https://github.com/ethyca/fides/pull/990).
* Added a "Custom" tag to distinguish user defined taxonomy fields from default taxonomy fields in the UI [#1027](https://github.com/ethyca/fides/pull/1027)

### Changed

* Upgraded base Docker version to Python 3.9 and updated all other references from 3.8 -> 3.9 [#974](https://github.com/ethyca/fides/pull/974)
* Prepend all database tables with `ctl_` [#979](https://github.com/ethyca/fides/pull/979)
* Moved the `admin-ui` code down one level into a `ctl` subdir [#970](https://github.com/ethyca/fides/pull/970)
* Extended the `/datamap` endpoint to include extra metadata [#992](https://github.com/ethyca/fides/pull/992)

## [1.8.1](https://github.com/ethyca/fides/compare/1.8.0...1.8.1) - 2022-08-08

### Deprecated

* The following environment variables have been deprecated, and replaced with the new environment variable names indicated below. To avoid breaking existing workflows, the deprecated variables are still respected in v1.8.1. They will be removed in a future release.
  * `FIDESCTL__API__DATABASE_HOST` --> `FIDESCTL__DATABASE__SERVER`
  * `FIDESCTL__API__DATABASE_NAME` --> `FIDESCTL__DATABASE__DB`
  * `FIDESCTL__API__DATABASE_PASSWORD` --> `FIDESCTL__DATABASE__PASSWORD`
  * `FIDESCTL__API__DATABASE_PORT` --> `FIDESCTL__DATABASE__PORT`
  * `FIDESCTL__API__DATABASE_TEST_DATABASE_NAME` --> `FIDESCTL__DATABASE__TEST_DB`
  * `FIDESCTL__API__DATABASE_USER` --> `FIDESCTL__DATABASE__USER`

### Developer Experience

* The included `docker-compose.yml` no longer references outdated ENV variables [#964](https://github.com/ethyca/fides/pull/964)

### Docs

* Minor release documentation now reflects the desired patch release process [#955](https://github.com/ethyca/fides/pull/955)
* Updated references to ENV variables [#964](https://github.com/ethyca/fides/pull/964)

### Fixed

* Deprecated config options will continue to be respected when set via environment variables [#965](https://github.com/ethyca/fides/pull/965)
* The git cache is rebuilt within the Docker container [#962](https://github.com/ethyca/fides/pull/962)
* The `wheel` pypi build no longer has a dirty version tag [#962](https://github.com/ethyca/fides/pull/962)
* Add setuptools to dev-requirements to fix versioneer error [#983](https://github.com/ethyca/fides/pull/983)

## [1.8.0](https://github.com/ethyca/fides/compare/1.7.1...1.8.0) - 2022-08-04

### Added

* Initial configuration wizard UI view
  * System scanning step: AWS credentials form and initial `generate` API usage.
  * System scanning results: AWS systems are stored and can be selected for review
* CustomInput type "password" with show/hide icon.
* Pull CLI command now checks for untracked/unstaged files in the manifests dir [#869](https://github.com/ethyca/fides/pull/869)
* Pull CLI command has a flag to pull missing files from the server [#895](https://github.com/ethyca/fides/pull/895)
* Add BigQuery support for the `generate` command and `/generate` endpoint [#814](https://github.com/ethyca/fides/pull/814) & [#917](https://github.com/ethyca/fides/pull/917)
* Added user auth tables [915](https://github.com/ethyca/fides/pull/915)
* Standardized API error parsing under `~/types/errors`
* Added taxonomy page to UI [#902](https://github.com/ethyca/fides/pull/902)
  * Added a nested accordion component for displaying taxonomy data [#910](https://github.com/ethyca/fides/pull/910)
* Add lru cache to get_config [927](https://github.com/ethyca/fides/pull/927)
* Add support for deprecated API config values [#959](https://github.com/ethyca/fides/pull/959)
* `fides` is now an alias for `fidesctl` as a CLI entrypoint [#926](https://github.com/ethyca/fides/pull/926)
* Add user auth routes [929](https://github.com/ethyca/fides/pull/929)
* Bump fideslib to 3.0.1 and remove patch code[931](https://github.com/ethyca/fides/pull/931)
* Update the `fidesctl` python package to automatically serve the UI [#941](https://github.com/ethyca/fides/pull/941)
* Add `push` cli command alias for `apply` and deprecate `apply` [943](https://github.com/ethyca/fides/pull/943)
* Add resource groups tagging api as a source of system generation [939](https://github.com/ethyca/fides/pull/939)
* Add GitHub Action to publish the `fidesctl` package to testpypi on pushes to main [#951](https://github.com/ethyca/fides/pull/951)
* Added configWizardFlag to ui to hide the config wizard when false [[#1453](https://github.com/ethyca/fides/issues/1453)

### Changed

* Updated the `datamap` endpoint to return human-readable column names as the first response item [#779](https://github.com/ethyca/fides/pull/779)
* Remove the `obscure` requirement from the `generate` endpoint [#819](https://github.com/ethyca/fides/pull/819)
* Moved all files from `fidesapi` to `fidesctl/api` [#885](https://github.com/ethyca/fides/pull/885)
* Moved `scan` and `generate` to the list of commands that can be run in local mode [#841](https://github.com/ethyca/fides/pull/841)
* Upgraded the base docker images from Debian Buster to Bullseye [#958](https://github.com/ethyca/fides/pull/958)
* Removed `ipython` as a dev-requirement [#958](https://github.com/ethyca/fides/pull/958)
* Webserver dependencies now come as a standard part of the package [#881](https://github.com/ethyca/fides/pull/881)
* Initial configuration wizard UI view
  * Refactored step & form results management to use Redux Toolkit slice.
* Change `id` field in tables from an integer to a string [915](https://github.com/ethyca/fides/pull/915)
* Update `fideslang` to `1.1.0`, simplifying the default taxonomy and adding `tags` for resources [#865](https://github.com/ethyca/fides/pull/865)
* Merge existing configurations with `fideslib` library [#913](https://github.com/ethyca/fides/pull/913)
* Moved frontend static files to `src/fidesctl/ui-build/static` [#934](https://github.com/ethyca/fides/pull/934)
* Replicated the error response handling from the `/validate` endpoint to the `/generate` endpoint [#911](https://github.com/ethyca/fides/pull/911)

### Developer Experience

* Remove `API_PREFIX` from fidesctl/core/utils.py and change references to `API_PREFIX` in fidesctl/api/reoutes/util.py [922](https://github.com/ethyca/fides/pull/922)

### Fixed

* Dataset field columns show all columns by default in the UI [#898](https://github.com/ethyca/fides/pull/898)
* Fixed the missing `.fides./` directory when locating the default config [#933](https://github.com/ethyca/fides/pull/933)

## [1.7.1](https://github.com/ethyca/fides/compare/1.7.0...1.7.1) - 2022-07-28

### Added

* Add datasets via YAML in the UI [#813](https://github.com/ethyca/fides/pull/813)
* Add datasets via database connection [#834](https://github.com/ethyca/fides/pull/834) [#889](https://github.com/ethyca/fides/pull/889)
* Add delete confirmation when deleting a field or collection from a dataset [#809](https://github.com/ethyca/fides/pull/809)
* Add ability to delete datasets from the UI [#827](https://github.com/ethyca/fides/pull/827)
* Add Cypress for testing [713](https://github.com/ethyca/fides/pull/833)
* Add datasets via database connection (UI only) [#834](https://github.com/ethyca/fides/pull/834)
* Add Okta support to the `/generate` endpoint [#842](https://github.com/ethyca/fides/pull/842)
* Add db support to `/generate` endpoint [849](https://github.com/ethyca/fides/pull/849)
* Added OpenAPI TypeScript client generation for the UI app. See the [README](/clients/admin-ui/src/types/api/README.md) for more details.

### Changed

* Remove the `obscure` requirement from the `generate` endpoint [#819](https://github.com/ethyca/fides/pull/819)

### Developer Experience

* When releases are published, dispatch a repository webhook event to ethyca/fidesctl-plus [#938](https://github.com/ethyca/fides/pull/938)

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
* FIDESOPS\_\_DEV_MODE for Easier SaaS Request Debugging [#363](https://github.com/ethyca/fidesops/pull/363)
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
