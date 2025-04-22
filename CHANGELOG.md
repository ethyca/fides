# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/)

The types of changes are:

- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Developer Experience` for changes in developer workflow or tooling.
- `Deprecated` for soon-to-be removed features.
- `Docs` for documentation only changes.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities.

Changes can also be flagged with a GitHub label for tracking purposes. The URL of the label should be put at the end of the entry. The possible labels are:
- https://github.com/ethyca/fides/labels/high-risk: to indicate that a change is a "high-risk" change that could potentially lead to unanticipated regressions or degradations
- https://github.com/ethyca/fides/labels/db-migration: to indicate that a given change includes a DB migration

## [Unreleased](https://github.com/ethyca/fides/compare/2.59.2...main)

### Added
- Migrate `Cookies` resources to `Asset` resources of type `Cookie` [#5776](https://github.com/ethyca/fides/pull/5776) https://github.com/ethyca/fides/labels/db-migration https://github.com/ethyca/fides/labels/high-risk
- Added support for selecting TCF Publisher Override configuration when configuring Privacy Experience [#6033](https://github.com/ethyca/fides/pull/6033)
- Added Google Cloud Storage as a storage option [#6006](https://github.com/ethyca/fides/pull/6006)
- Update the Datahub Permissions section to include required permissions from Datahub [#6052](https://github.com/ethyca/fides/pull/6052)
- Added assumed role arn capabilities to aws Storage [#6027](https://github.com/ethyca/fides/pull/6027)
- Added the ability to create new TCF Experiences within Admin UI [#6055](https://github.com/ethyca/fides/pull/6055)
- PostgreSQL connection config now supports SSL Mode [#6068](https://github.com/ethyca/fides/pull/6068)

### Changed
- Changed how TCF Publisher Overrides gets configured in consent settings [#6013](https://github.com/ethyca/fides/pull/6013)
- Frontend now do not generate `key` when creating a Website Monitor [#6041](https://github.com/ethyca/fides/pull/6041)
- Integrations manage modals now are cappable of showing a small description [#6037](https://github.com/ethyca/fides/pull/6037)
- UI now allows assigning of non-consent-category data uses to system assets [#6049](https://github.com/ethyca/fides/pull/6049)
- Updated bulk ignore assets toast message [#6043](https://github.com/ethyca/fides/pull/6043)
- Updated UI behavior for editing languages in the Experience config for consistency and clarity [#6055](https://github.com/ethyca/fides/pull/6055)
- Moved detection & discovery features out of beta [#6059](https://github.com/ethyca/fides/pull/6059)

### Developer Experience
- Reduced animations on Cypress tests in Privacy Center for quicker results [#5976](https://github.com/ethyca/fides/pull/5976)
- Migrated Tooltip components to Ant Design across Admin UI [#6060](https://github.com/ethyca/fides/pull/6060)
- Added custom Typography component to FidesUI with configurable text sizes [#6062](https://github.com/ethyca/fides/pull/6062)
- Updated the Docker image used for MSSQL integration tests [#6063](https://github.com/ethyca/fides/pull/6063)
- Improved Docker image build times by using separate amd64/arm64 Github runners [#6073](https://github.com/ethyca/fides/pull/6073)

### Fixed
- Fixed typo in Vermont US state name [#6029](https://github.com/ethyca/fides/pull/6029)
- Fixed two Georgia's in regions list and incorrect name for the state SD [#6036](https://github.com/ethyca/fides/pull/6036)
- Fixed performance issues in Data map report in Admin UI [#6046](https://github.com/ethyca/fides/pull/6046)
- Fixed details requirements in AWS SES setup [#6047](https://github.com/ethyca/fides/pull/6047)
- Addressed some performance issues with Experience configuration previews [#6055](https://github.com/ethyca/fides/pull/6055)

## [2.59.2](https://github.com/ethyca/fides/compare/2.59.1...2.59.2)

### Added
- Added PostgreSQL connection config form to the "integrations" page to support use with discovery monitors [#6018](https://github.com/ethyca/fides/pull/6018)
- Added SSL Mode field for MySQL connections [#6048](https://github.com/ethyca/fides/pull/6048)

### Changed
- Removed `dbname` as a required field for PostgreSQL connection configs to support use with discovery monitors [#6018](https://github.com/ethyca/fides/pull/6018)
- Updated consent automation models to support echo detection in Fidesplus [#6054](https://github.com/ethyca/fides/pull/6054)

### Fixed
- Fixed Privacy Center issue where unconfigured fields (eg. phone) were being passed as null form values [#6045](https://github.com/ethyca/fides/pull/6045)
- Fixed startup issues with Celery workers [#6058](https://github.com/ethyca/fides/pull/6058)

## [2.59.1](https://github.com/ethyca/fides/compare/2.59.0...2.59.1)

### Added
- Adds embedded-consent route to Privacy Center [#6040](https://github.com/ethyca/fides/pull/6040)

## [2.59.0](https://github.com/ethyca/fides/compare/2.58.2...2.59.0)

### Added
- Added `reject_all_mechanism` to `PrivacyExperienceConfig` [#5952](https://github.com/ethyca/fides/pull/5952) https://github.com/ethyca/fides/labels/db-migration
- Added DataHub dataset sync functionality UI with feedback and error handling [#5949](https://github.com/ethyca/fides/pull/5949)
- Added support for TCF preview in Admin UI experience form [#5962](https://github.com/ethyca/fides/pull/5962)
- Added `opt_in_only` to `Layer1ButtonOption` [#5958](https://github.com/ethyca/fides/pull/5958)
- Added support for links in `<a>` tags on the custom HTML description [#5960](https://github.com/ethyca/fides/pull/5960)
- Added "Reject all" behavior and visibility options to TCF Experience config form [#5964](https://github.com/ethyca/fides/pull/5964)
- Added `TCFConfiguration` and `TCFPublisherRestriction` models [#5983](https://github.com/ethyca/fides/pull/5983) https://github.com/ethyca/fides/labels/db-migration
- Added tab navigation to action center system aggregate table [#6011](https://github.com/ethyca/fides/pull/6011)
- Support `Quarterly` and `Yearly` monitor scheduling [#5981](https://github.com/ethyca/fides/pull/5981)
- Adds integration tests for Enterprise Bigquery DSR nested fields [#5969](https://github.com/ethyca/fides/pull/5969)
- Added `tcf_configuration_id` to `PrivacyExperienceConfig` and fixes `TCFPublisherRestriction` validations [#6012](https://github.com/ethyca/fides/pull/6012) https://github.com/ethyca/fides/labels/db-migration
- Added a `--separate-files` flag to the `fides pull dataset` CLI command to pull each dataset into its own file [#6007](https://github.com/ethyca/fides/pull/6007)
- Added a `readonly_server` database setting to support specifying a read-only database [#6023](https://github.com/ethyca/fides/pull/6023)

### Changed
- Bumped Next.js for all frontend apps to latest patch versions. [#5946](https://github.com/ethyca/fides/pull/5946)
- Updating UI for Integrations, the tags now represent capabilities of the integrations [#5973](https://github.com/ethyca/fides/pull/5973)
- Changed action center result tables to use expandable cells for multi-value results [#5963](https://github.com/ethyca/fides/pull/5963)
- Changed action center homepage to use CSS grid layout [#5982](https://github.com/ethyca/fides/pull/5982)
- Updated the UI for the activity tab of the privacy request detail page [#6005](https://github.com/ethyca/fides/pull/6005)
- Unified frontend formatKey method, so its behavior is closer to the backend behavior [#6010](https://github.com/ethyca/fides/pull/6010)
- Action center table's checkboxes were improved, also improved change indications [#6021](https://github.com/ethyca/fides/pull/6021)

### Fixed
- Updated relationships for Comments, Attachments and PrivacyRequests to remove overlap sqlalchemy error. [#5929](https://github.com/ethyca/fides/pull/5929)
- Hide "Reclassify" option on fields in D&D tables [#5956](https://github.com/ethyca/fides/pull/5956)
- Fix D&D action errors not surfacing in UI [#5997](https://github.com/ethyca/fides/pull/5997)
- Fixes translation bug in TCF custom notices [#6003](https://github.com/ethyca/fides/pull/6003)
- Fixed issue with SaaS integration update payloads [#6001](https://github.com/ethyca/fides/pull/6001)
- Fix non-consent-category data uses showing up in system assets table [#5999](https://github.com/ethyca/fides/pull/5999)
- Fix `TCFConfiguration` relationship definitions [#6031](https://github.com/ethyca/fides/pull/6031)

### Removed
- Removed datasetClassificationUpdates flag from admin UI. [#5950](https://github.com/ethyca/fides/pull/5950)

## [2.58.2](https://github.com/ethyca/fides/compare/2.58.1...2.58.2)

### Changed
- Writes fides consent cookie during OT consent migration [#6009](https://github.com/ethyca/fides/pull/6009)

## [2.58.1](https://github.com/ethyca/fides/compare/2.58.0...2.58.1)

### Fixed
- Fixed an issue with banner dismisal resulting in resurfaced banner [#5979](https://github.com/ethyca/fides/pull/5979)

## [2.58.0](https://github.com/ethyca/fides/compare/2.57.1...2.58.0)

### Added
- Support for location based privacy center actions [#5803](https://github.com/ethyca/fides/pull/5803)
- Added `is_country` field on locations [#5885](https://github.com/ethyca/fides/pull/5885)
- Added `page` column to `Asset` table/model [#5898](https://github.com/ethyca/fides/pull/5898) https://github.com/ethyca/fides/labels/db-migration
- Added new `has_next` parameter for the `cursor` pagination strategy [#5888](https://github.com/ethyca/fides/pull/5888)
- Support `FIDES_PRIVACY_CENTER__FIDES_JS_MAX_AGE_SECONDS` configuration option for `fides-privacy-center` to override default cache duration for /fides.js [#5909](https://github.com/ethyca/fides/pull/5909)
- Add properties for user assigned systems/data_uses on staged resources [5841](https://github.com/ethyca/fides/pull/5841) https://github.com/ethyca/fides/labels/db-migration
- Added tooltips to the buttons in the dataset test UI [#5899](https://github.com/ethyca/fides/pull/5899)
- Added the ability to stop a test privacy request in the dataset test UI [#5901](https://github.com/ethyca/fides/pull/5901)
- Support setting publisher country code in Consent Settings [#5902](https://github.com/ethyca/fides/pull/5902)
- Added option for disabling consent notice toggles [#5872](https://github.com/ethyca/fides/pull/5872)
- Added UI to manually update Assets in the system asset view [#5914](https://github.com/ethyca/fides/pull/5914)
- Use the experience's `tcf_publisher_country_code` when building TC strings [#5921](https://github.com/ethyca/fides/pull/5921)
- Added size thresholds to S3 upload and retrieval methods for more efficient document processing. [#5922](https://github.com/ethyca/fides/pull/5922)
- Added support for Notice Consent String integration in Fides String [#5895](https://github.com/ethyca/fides/pull/5895)
- Added support for new options for Fides.gtm method [#5917](https://github.com/ethyca/fides/pull/5917)
- Added tab-based filtering and row persistence to web monitor assets table [#5933](https://github.com/ethyca/fides/pull/5933)
- Add inline editing for system assets table [#5940](https://github.com/ethyca/fides/pull/5940)

### Changed
- Privacy Center was updated to use React 19 and Nextjs 15 [#5803](https://github.com/ethyca/fides/pull/5803) https://github.com/ethyca/fides/labels/high-risk
- Change `Browser Request` values to `Browser request` in Asset and StagedResource models [#5898](https://github.com/ethyca/fides/pull/5898) https://github.com/ethyca/fides/labels/db-migration
- Changed discovered asset "system" cell to use `user_assigned_system_key` property [#5908](https://github.com/ethyca/fides/pull/5908)
- Changed Dataset endpoint, it now has `minimal` parameter, and can be filtered by `fides_meta.namespace.connection_type` [#5915](https://github.com/ethyca/fides/pull/5915)
- Datahub integration now allows datasets to be selected [#5926](https://github.com/ethyca/fides/pull/5926)
- Enable Consent Reporting screen by default. Update consent lookup table column. [#5936](https://github.com/ethyca/fides/pull/5936)

### Fixed
- Fixed UX issues with website monitor form [#5884](https://github.com/ethyca/fides/pull/5884)
- Fixed consent reporting table issues, add external id column [#5918](https://github.com/ethyca/fides/pull/5918)
- Removed excessive authorization debug logs [#5920](https://github.com/ethyca/fides/pull/5920)
- Fixed fix incorrect calls to TCF api update method [#5916](https://github.com/ethyca/fides/pull/5916)
- Fixed "unvisited edges" error when dealing with optional identities [#5923](https://github.com/ethyca/fides/pull/5923)
- Fixed issue where sometimes an experience translation couldn't be added [#5942](https://github.com/ethyca/fides/pull/5942)

### Removed
- Removed beta flag for Datahub feature [#5937](https://github.com/ethyca/fides/pull/5937)

## [2.57.1](https://github.com/ethyca/fides/compare/2.57.0...2.57.1)

### Changed
- Added extra debug logging and fixed handler time calculation [#5927](https://github.com/ethyca/fides/pull/5927)

## [2.57.0](https://github.com/ethyca/fides/compare/2.56.2...2.57.0)

### Added
- DB model support for Attachments [#5784](https://github.com/ethyca/fides/pull/5784) https://github.com/ethyca/fides/labels/db-migration
- DB migration to add `description` column to `asset` [#5822](https://github.com/ethyca/fides/pull/5822) https://github.com/ethyca/fides/labels/db-migration
- DB model support for messages on `MonitorExecution` records [#5846](https://github.com/ethyca/fides/pull/5846) https://github.com/ethyca/fides/labels/db-migration
- Added support for GPP String integration in Fides String [#5845](https://github.com/ethyca/fides/pull/5845)
- Attachments storage capabilities (S3 or local) [#5812](https://github.com/ethyca/fides/pull/5812) https://github.com/ethyca/fides/labels/db-migration
- DB model support for Comments [#5833](https://github.com/ethyca/fides/pull/5833/files) https://github.com/ethyca/fides/labels/db-migration
- Added UI for configuring website integrations and monitors [#5867](https://github.com/ethyca/fides/pull/5867)
- Adding support for BigQuery struct updates [#5849](https://github.com/ethyca/fides/pull/5849)
- Added support for OneTrust Consent Migration [#5873](https://github.com/ethyca/fides/pull/5873)

### Changed
- Bumped supported Python versions to `3.10.16` and `3.9.21` [#5840](https://github.com/ethyca/fides/pull/5840)
- Update the privacy request detail page to a new layout and improved styling [#5824](https://github.com/ethyca/fides/pull/5824)
- Updated privacy request handling to still succeed if not all identities are provided [#5836](https://github.com/ethyca/fides/pull/5836)
- Refactored privacy request processing to never re-use sessions [#5862](https://github.com/ethyca/fides/pull/5862)
- Updated hover state of menu items to be more visible [#5868](https://github.com/ethyca/fides/pull/5868)
- Use `gpp_settings.cmp_api_required` to determine if GPP CMP API should be included in bundle [#5883](https://github.com/ethyca/fides/pull/5883)
- Updates Fides interface docs to expose additional fields [#5878](https://github.com/ethyca/fides/pull/5878)

### Developer Experience
- Moved non-prod Admin UI dependencies to devDependencies [#5832](https://github.com/ethyca/fides/pull/5832)
- Prevent Admin UI and Privacy Center from starting when running `nox -s dev` with datastore params [#5843](https://github.com/ethyca/fides/pull/5843)
- Remove plotly (unused package) to reduce fides image size [#5852](https://github.com/ethyca/fides/pull/5852)
- Fixed issue where the log_context decorator didn't support positional arguments [#5866](https://github.com/ethyca/fides/pull/5866)

### Fixed
- Fixed pagination bugs on some tables [#5819](https://github.com/ethyca/fides/pull/5819)
- Fixed load_samples to wrap variables in quotes to prevent YAML parsing errors [#5857](https://github.com/ethyca/fides/pull/5857)
- Fixed incorrect value being set for `MonitorExecution.started` column [#5864](https://github.com/ethyca/fides/pull/5864)
- Improved the behavior and state management of MSPA-related settings [#5861](https://github.com/ethyca/fides/pull/5861)
- Fixed CORS origins handling to be more consistent across config (toml/env var) and API settings; allow `0.0.0.0` as an origin [#5853](https://github.com/ethyca/fides/pull/5853)
- Fixed an issue with the update payloads for select SaaS integrations [#5860](https://github.com/ethyca/fides/pull/5860)
- Fixed `/privacy-request/<id>/resubmit` endpoint so it doesn't queue the request twice [#5870](https://github.com/ethyca/fides/pull/5870)
- Fixed the system assets table being the wrong width [#5879](https://github.com/ethyca/fides/pull/5879)
- Fixed vendor override handling in FidesJS CMP [#5886](https://github.com/ethyca/fides/pull/5886)
- Fix `extraDetails.preference` on `FidesUIChanged` events from FidesJS SDK to include the correct `notice_key` when using custom purposes in TCF experience [#5892](https://github.com/ethyca/fides/pull/5892)

## [2.56.2](https://github.com/ethyca/fides/compare/2.56.1...2.56.2)

### Added
- Update FidesJS to push all `FidesEvent` types to GTM (except `FidesInitializing`) [#5821](https://github.com/ethyca/fides/pull/5821)
- Added a consent reporting table and consent lookup feature [#5839](https://github.com/ethyca/fides/pull/5839)
- Added a high-precision `timestamp` to all `FidesEvents` from FidesJS SDK [#5859](https://github.com/ethyca/fides/pull/5859)
- Added a `extraDetails.trigger` to `FidesUIChanged` events from FidesJS SDK with info about the UI element that triggered the event [#5859](https://github.com/ethyca/fides/pull/5859)
- Added a `extraDetails.preference` to `FidesUIChanged` events from FidesJS SDK with info about the preference that was changed (notice, TCF purpose, TCF vendor, etc.) [#5859](https://github.com/ethyca/fides/pull/5859)

### Fixed
- Addressed TCModel console error when opting into some purposes [#5850](https://github.com/ethyca/fides/pull/5850)
- Opt out of all in TCF no longer affects "notice only" notices [#5850](https://github.com/ethyca/fides/pull/5850)
- Corrected the Tag color for some columns of the Privacy requests table. [#5848](https://github.com/ethyca/fides/pull/5848)

## [2.56.1](https://github.com/ethyca/fides/compare/2.56.0...2.56.1)

### Changed
- Custom TCF purposes respect NOTICE_ONLY [#5830](https://github.com/ethyca/fides/pull/5830)

### Fixed
- Fixed usage of stale DB sessions when running privacy requests [#5834](https://github.com/ethyca/fides/pull/5834)

## [2.56.0](https://github.com/ethyca/fides/compare/2.55.4...2.56.0)

### Added
- DB model support for Web Monitoring [#5616](https://github.com/ethyca/fides/pull/5616) https://github.com/ethyca/fides/labels/db-migration
- Added support for queue-specific Celery workers [#5761](https://github.com/ethyca/fides/pull/5761)
- Added support for AWS SES as an email provider [#5804](https://github.com/ethyca/fides/pull/5804)
- Nested identity query support for BigQuery [#5814](https://github.com/ethyca/fides/pull/5814)
- Added job that automatically requeues interrupted tasks for in progress privacy requests [#5800](https://github.com/ethyca/fides/pull/5800)
- Added "Assets" tab on system view for web monitor assets [#5811](https://github.com/ethyca/fides/pull/5811)
- Support for MySQL Data Detection & Discovery Monitors [#5798](https://github.com/ethyca/fides/pull/5798)

### Changed
- Improved dataset validation for namespace metadata and dataset reachability [#5744](https://github.com/ethyca/fides/pull/5744)
- Taxonomy page can now be accessed by users with only read permissions [#5815](https://github.com/ethyca/fides/pull/5815)

### Developer Experience
- Modified Dependabot configuration to support monorepo security updates [#5810](https://github.com/ethyca/fides/pull/5810)
- Fix load_samples to correctly collect & load sample connections with "False" secret values [#5828](https://github.com/ethyca/fides/pull/5828)

### Docs
- Removed version pins in LDFLAGS & CFLAGS for local MSSQL builds [#5760](https://github.com/ethyca/fides/pull/5760)

### Fixed
- Fixed background color of the message indicating the rows selected [#5847](https://github.com/ethyca/fides/pull/5847)
- Fixed bug with D&D table column widths [#5813](https://github.com/ethyca/fides/pull/5813)
- Fixed `poll_for_exited_privacy_request_tasks` for DSR-processing improvements [#5820](https://github.com/ethyca/fides/pull/5820)

## [2.55.4](https://github.com/ethyca/fides/compare/2.55.3...2.55.4)

### Added
- Added setting to control fuzzy search for privacy requests [#5748](https://github.com/ethyca/fides/pull/5748)

### Fixed
- Fixed BQ partition clause validation to allow `-` characters in operands [#5796](https://github.com/ethyca/fides/pull/5796)

## [2.55.3](https://github.com/ethyca/fides/compare/2.55.2...2.55.3)

### Fixed
- Fixed BigQuery DSR integration generates invalid queries when having a dataset with nested fields [#5785](https://github.com/ethyca/fides/pull/5785)

## [2.55.2](https://github.com/ethyca/fides/compare/2.55.1...2.55.2)

### Changed
- Release version bump. No code changes.

## [2.55.1](https://github.com/ethyca/fides/compare/2.55.0...2.55.1)

### Fixed
- Fixed GPP string and section inconsistencies [#5765](https://github.com/ethyca/fides/pull/5765)
- Fixed sending of notifications for privacy request receipts [#5777](https://github.com/ethyca/fides/pull/5777)
- Fixed create systems with vendor_deleted_at field [#5786](https://github.com/ethyca/fides/pull/5786)

## [2.55.0](https://github.com/ethyca/fides/compare/2.54.0...2.55.0)

### Added
- Added editing support for categories of consent on discovered assets [#5739](https://github.com/ethyca/fides/pull/5739)
- Added a read-only consent category cell to Action Center aggregate system results table [#5737](https://github.com/ethyca/fides/pull/5737)
- Added detail trays to items in data catalog view [#5729](https://github.com/ethyca/fides/pull/5729)
- Support rendering and saving consent from custom notices in TCF Overlay [#5742](https://github.com/ethyca/fides/pull/5742)
- Added worker stats endpoint to monitor worker status and task queue length [#5725](https://github.com/ethyca/fides/pull/5725)
- New "Headless" experience type to support custom UI implementations [#5751](https://github.com/ethyca/fides/pull/5751)

### Changed
- Added frequency field to DataHubSchema integration config [#5716](https://github.com/ethyca/fides/pull/5716)
- Added glossary_node field to DataHubSchema integration config [#5734](https://github.com/ethyca/fides/pull/5734)
- Added initial support for upcoming "headless" CMP experience type [#5731](https://github.com/ethyca/fides/pull/5731)
- All Select dropdowns will now allow searching to narrow down the options by default [#5738](https://github.com/ethyca/fides/pull/5738)
- Exposes privacy notice picker for TCF components [#5730](https://github.com/ethyca/fides/pull/5730)
- Model changes to support new privacy center config options [5732](https://github.com/ethyca/fides/pull/5732)

### Fixed
- Fixed `fides annotate dataset` command enters incorrect value on the `direction` field. [#5727](https://github.com/ethyca/fides/pull/5727)
- Fixed Bigquery flakey tests. [#5713](https://github.com/ethyca/fides/pull/5713)
- Fixed breadcrumb navigation issues in data catalog view [#5717](https://github.com/ethyca/fides/pull/5717)
- Fixed `window.Fides.experience` of FidesJS to be a merged version of the minimal and full experience. [#5726](https://github.com/ethyca/fides/pull/5726)
- Fixed vendor count template string on FidesJS embedded layer 2 descriptions [#5736](https://github.com/ethyca/fides/pull/5736)
- Allowing a list with a single dataset in the YAML dataset editor [#5750](https://github.com/ethyca/fides/pull/5750)
- Fixed edge case translation string issue on FidesJS embedded layer 2 [#5749](https://github.com/ethyca/fides/pull/5749)
- Standardized taxonomy endpoint behavior for URLs with and without trailing slashes to ensure all endpoints properly enforce the latest data validation rules [#5753](https://github.com/ethyca/fides/pull/5753)

## [2.54.0](https://github.com/ethyca/fides/compare/2.53.0...2.54.0)

### Added
- Migration to add the `data_uses` column to `stagedresource` table, prereqs for Data Catalog work in Fidesplus [#5600](https://github.com/ethyca/fides/pull/5600/) https://github.com/ethyca/fides/labels/db-migration
- Added a new endpoint to fully resubmit any errored privacy requests [#5658](https://github.com/ethyca/fides/pull/5658) https://github.com/ethyca/fides/labels/db-migration
- Migration to add the `monitorexecution` table used by fidesplus to persist `MonitorExecution` records to DB [#5704](https://github.com/ethyca/fides/pull/5704) https://github.com/ethyca/fides/labels/db-migration

### Changed
- Updated UI colors to new brand. Update logo, homepage cards. [#5668](https://github.com/ethyca/fides/pull/5668)
- Privacy request status tags colors have been updated [#5699](https://github.com/ethyca/fides/pull/5699)
- The privacy declarations for a system are now sorted alphabetically by name. [#5683](https://github.com/ethyca/fides/pull/5683)
- Upgraded GPP library to `3.1.5` and added support for all available state sections (ustx, usde, usia, etc.) [#5696](https://github.com/ethyca/fides/pull/5696)
- Updating DSR execution to allow collections to be unreachable when they don't contain policy-relevant data categories [#5689](https://github.com/ethyca/fides/pull/5689)
- Added "All activity" root breadcrumb to D&D results tables [#5694](https://github.com/ethyca/fides/pull/5694)

### Developer Experience
- Migrated radio buttons and groups to Ant Design [#5681](https://github.com/ethyca/fides/pull/5681)

### Fixed
- Updating mongodb connectors so it can support usernames and password with URL encoded characters [#5682](https://github.com/ethyca/fides/pull/5682)
- After creating a new system, the url is now updated correctly to the new system edit page [#5701](https://github.com/ethyca/fides/pull/5701)
- Visual fixes for table header buttons [#5693](https://github.com/ethyca/fides/pull/5693)

## [2.53.0](https://github.com/ethyca/fides/compare/2.52.0...2.53.0)

### Added
- Added Action Center MVP behind new feature flag [#5622](https://github.com/ethyca/fides/pull/5622)
- Added Data Catalog MVP behind new feature flag [#5628](https://github.com/ethyca/fides/pull/5628)
- Added cache-clearing methods to the `DBCache` model to allow deleting cache entries [#5629](https://github.com/ethyca/fides/pull/5629)
- Adds partitioning, custom identities, multiple identities to test coverage for BigQuery Enterprise [#5618](https://github.com/ethyca/fides/pull/5618)
- Added Datahub groundwork required by Fidesplus [#5666](https://github.com/ethyca/fides/pull/5666)

### Changed
- Updated brand link url [#5656](https://github.com/ethyca/fides/pull/5656)
- Changed "Reclassify" D&D button to show in an overflow menu when row actions are overcrowded [#5655](https://github.com/ethyca/fides/pull/5655)
- Removed primary key requirements for BigQuery and Postgres erasures [#5591](https://github.com/ethyca/fides/pull/5591)
- Updated `DBCache` model so setting cache value always updates the updated_at field [#5669](https://github.com/ethyca/fides/pull/5669)
- Changed sizes of buttons in table headers [#5654](https://github.com/ethyca/fides/pull/5654)
- Adds new config for max number of rows in DSR download through Admin-UI [#5671](https://github.com/ethyca/fides/pull/5671)
- Added CSS variable to FidesJS: `--fides-base-font-size: 16px` for better consistency. Overriding this variable with "1rem" will mimic legacy behavior. [#5673](https://github.com/ethyca/fides/pull/5673) https://github.com/ethyca/fides/labels/high-risk

### Fixed
- Fixed issue where the custom report "reset" button was not working as expected [#5649](https://github.com/ethyca/fides/pull/5649)
- Fixed column ordering issue in the Data Map report [#5649](https://github.com/ethyca/fides/pull/5649)
- Fixed issue where the Data Map report filter dialog was missing an Accordion item label [#5649](https://github.com/ethyca/fides/pull/5649)
- Improved database session management for long running access request tasks [#5667](https://github.com/ethyca/fides/pull/5667)
- Ensured decode_password function properly handles plaintext but valid base64 passwords [#5698](https://github.com/ethyca/fides/pull/5698)

## [2.52.0](https://github.com/ethyca/fides/compare/2.51.2...2.52.0)

### Added
- New page in the Cookie House sample app to demonstrate the use of embedding the FidesJS SDK on the page [#5564](https://github.com/ethyca/fides/pull/5564)
- Added event based communication example to the Cookie House sample app [#5597](https://github.com/ethyca/fides/pull/5597)
- Added new erasure tests for BigQuery Enterprise [#5554](https://github.com/ethyca/fides/pull/5554)
- Added new `has_next` parameter for the `link` pagination strategy [#5596](https://github.com/ethyca/fides/pull/5596)
- Added a `DBCache` model for database-backed caching [#5613](https://github.com/ethyca/fides/pull/5613) https://github.com/ethyca/fides/labels/db-migration
- Adds "reclassify" button to discovery result tables [#5574](https://github.com/ethyca/fides/pull/5574)
- Added support for exporting datamaps with column renaming, reordering and visibility options [#5543](https://github.com/ethyca/fides/pull/5543)

### Changed
- Adjusted Ant's Select component colors and icon [#5594](https://github.com/ethyca/fides/pull/5594)
- Replaced taxonomies page with new UI based on an interactive tree visualization [#5602](https://github.com/ethyca/fides/pull/5602)
- Adjusted functionality around updating taxonomy active field, includes data migration to re-activate taxonomy nodes [#5617](https://github.com/ethyca/fides/pull/5617)
- Migrated breadcrumbs to Ant Design [#5610](https://github.com/ethyca/fides/pull/5610)
- Updated `CustomReportConfig` to be more intuitive on its contents [#5543](https://github.com/ethyca/fides/pull/5543)

### Fixed
- Fixing quickstart.py script [#5585](https://github.com/ethyca/fides/pull/5585)
- Removed unnecessary double notification when updating database integrations [#5612](https://github.com/ethyca/fides/pull/5612)

## [2.51.2](https://github.com/ethyca/fides/compare/2.51.1...2.51.2)

### Fixed
- Fixed miscellaneous performance issues with Systems and PrivacyDeclarations [#5601](https://github.com/ethyca/fides/pull/5601)

## [2.51.1](https://github.com/ethyca/fides/compare/2.51.0...2.51.1)

### Fixed
- SaaS integrations using `oauth_client_credentials` now properly update their access token when editing the secrets. [#5548](https://github.com/ethyca/fides/pull/5548)
- Saas integrations using `oauth_client_credentials` now properly refresh their access token when the current token expires [#5569](https://github.com/ethyca/fides/pull/5569)
- Adding `dsr_testing_tools_enabled` security setting [#5573](https://github.com/ethyca/fides/pull/5573)
- Reverted elimination of connection pool in worker tasks to prevent DB performance issues [#5592](https://github.com/ethyca/fides/pull/5592)

## [2.51.0](https://github.com/ethyca/fides/compare/2.50.0...2.51.0)

### Added
- Added new column for Action Type in privacy request event logs [#5546](https://github.com/ethyca/fides/pull/5546)
- Added `fides_consent_override` option in FidesJS SDK [#5541](https://github.com/ethyca/fides/pull/5541)
- Added new `script` ConsentMethod in FidesJS SDK for tracking automated consent [#5541](https://github.com/ethyca/fides/pull/5541)
- Added a new page under system integrations to run standalone dataset tests (Fidesplus) [#5549](https://github.com/ethyca/fides/pull/5549)

### Changed
- Adding hashes to system tab URLs [#5535](https://github.com/ethyca/fides/pull/5535)
- Boolean inputs will now show as a select with true/false values in the connection form [#5555](https://github.com/ethyca/fides/pull/5555)
- Updated Cookie House to be responsive [#5541](https://github.com/ethyca/fides/pull/5541)
- Updated `/system` endpoint to filter vendor deleted systems [#5553](https://github.com/ethyca/fides/pull/5553)

### Developer Experience
- Migrated remaining instances of Chakra's Select component to use Ant's Select component [#5502](https://github.com/ethyca/fides/pull/5502)

### Fixed
- Updating dataset PUT to allow deleting all datasets [#5524](https://github.com/ethyca/fides/pull/5524)
- Adds support for fides_key generation when parent_key is provided in Taxonomy create endpoints [#5542](https://github.com/ethyca/fides/pull/5542)
- An integration will no longer re-enable after saving the connection form [#5555](https://github.com/ethyca/fides/pull/5555)
- Fixed positioning of Fides brand link in privacy center [#5572](https://github.com/ethyca/fides/pull/5572)

### Removed
- Removed unnecessary debug logging from the load_file config helper [#5544](https://github.com/ethyca/fides/pull/5544)


## [2.50.0](https://github.com/ethyca/fides/compare/2.49.1...2.50.0)

### Added
- Added namespace support for Snowflake [#5486](https://github.com/ethyca/fides/pull/5486)
- Added support for field-level masking overrides [#5446](https://github.com/ethyca/fides/pull/5446)
- Added BigQuery Enterprise access request integration test [#5504](https://github.com/ethyca/fides/pull/5504)
- Added MD5 email hashing for Segment's Right to Forget endpoint requests [#5514](https://github.com/ethyca/fides/pull/5514)
- Added loading state to the toggle switches on the Privacy experiences page [#5529](https://github.com/ethyca/fides/pull/5529)
- Added new env variable to set a privacy center to default to a specific property  [#5532](https://github.com/ethyca/fides/pull/5532)

### Changed
- Allow hiding systems via a `hidden` parameter and add two flags on the `/system` api endpoint; `show_hidden` and `dnd_relevant`, to display only systems with integrations [#5484](https://github.com/ethyca/fides/pull/5484)
- The CMP override `fides_privacy_policy_url` will now apply even if the `fides_override_language` doesn't match [#5515](https://github.com/ethyca/fides/pull/5515)
- Updated POST taxonomy endpoints to handle creating resources without specifying fides_key [#5468](https://github.com/ethyca/fides/pull/5468)
- Disabled connection pooling for task workers and added retries and keep-alive configurations for database connections [#5448](https://github.com/ethyca/fides/pull/5448) https://github.com/ethyca/fides/labels/high-risk
- Added timeout handling in the UI for async discovery monitor-related queries [#5519](https://github.com/ethyca/fides/pull/5519)

### Developer Experience
- Migrated several instances of Chakra's Select component to use Ant's Select component [#5475](https://github.com/ethyca/fides/pull/5475)
- Fixing BigQuery integration tests [#5491](https://github.com/ethyca/fides/pull/5491)
- Enhanced logging for privacy requests [#5500](https://github.com/ethyca/fides/pull/5500)

### Docs
- Added docs for PrivacyNoticeRegion type [#5488](https://github.com/ethyca/fides/pull/5488)

### Fixed
- Fixed deletion of ConnectionConfigs that have related MonitorConfigs [#5478](https://github.com/ethyca/fides/pull/5478)
- Fixed extra delete icon on Domains page [#5513](https://github.com/ethyca/fides/pull/5513)
- Fixed incorrect display names on some D&D resources [#5498](https://github.com/ethyca/fides/pull/5498)
- Fixed position of "Integration" button on system detail page [#5497](https://github.com/ethyca/fides/pull/5497)
- Fixing issue where "privacy request received" emails would not be sent if the request had custom identities [#5518](https://github.com/ethyca/fides/pull/5518)
- Fixed issue with long-running privacy request tasks losing their connection to the database [#5500](https://github.com/ethyca/fides/pull/5500)
- Fixed missing "Manage privacy preferences" button label option in TCF experience translations [#5528](https://github.com/ethyca/fides/pull/5528)
- Fixed privacy center not fetching the correct experience when using custom property paths  [#5532](https://github.com/ethyca/fides/pull/5532)

### Security
 - Password Policy is now Enforced in Accept Invite API [CVE-2024-52008](https://github.com/ethyca/fides/security/advisories/GHSA-v7vm-rhmg-8j2r)

## [2.49.1](https://github.com/ethyca/fides/compare/2.49.0...2.49.1)

### Added
- Added support for GPP national string to be used alongside state-by-state using a new approach option [#5480](https://github.com/ethyca/fides/pull/5480)
- Added "Powered by" branding link to privacy center and Layer 2 CMP [#5483](https://github.com/ethyca/fides/pull/5483)
- Added loading state to the toggle switches on the Manage privacy notices page [#5489](https://github.com/ethyca/fides/pull/5489)
- Support BlueConic objectives [#5479](https://github.com/ethyca/fides/pull/5479)

### Fixed
- Use BlueConic Profile API correctly. [#5487](https://github.com/ethyca/fides/pull/5487)
- Fixed a bug where branding link was sometimes misaligned [#5496](https://github.com/ethyca/fides/pull/5496)

## [2.49.0](https://github.com/ethyca/fides/compare/2.48.2...2.49.0)

### Added
- Added DataHub integration config [#5401](https://github.com/ethyca/fides/pull/5401)
- Added keepalive settings to the Redshift integration [#5433](https://github.com/ethyca/fides/pull/5433)
- Remediation endpoint `/datasets/clean` to clean up dataset names generated with previous version of fides nested field support [#5461](https://github.com/ethyca/fides/pull/5461)

### Changed
- Migrated the base Select component for Vendor selection to Ant Design [#5459](https://github.com/ethyca/fides/pull/5459)
- Added a security setting that must be set to true to enable the access request download feature [#5451](https://github.com/ethyca/fides/pull/5451)
- Preventing erasures for the Zendesk integration if there are any open tickets [#5429](https://github.com/ethyca/fides/pull/5429)
- Updated look/feel of all badges in the Data map report [#5464](https://github.com/ethyca/fides/pull/5464)
- Allow adding data categories to nested fields [#5434](https://github.com/ethyca/fides/pull/5434)

### Fixed
 - Fix rendering of subfield names in D&D tables [#5439](https://github.com/ethyca/fides/pull/5439)
 - Fix "Save" button on system source/destination page not working [#5469](https://github.com/ethyca/fides/pull/5469)
 - Updating Salesforce erasure request with overrides so it properly passes validation. Removing Account endpoint since it does not contain user data [#5452](https://github.com/ethyca/fides/pull/5452)
 - Fix Pytest-Ctl-External tests [#5457](https://github.com/ethyca/fides/pull/5457)

### Developer Experience
- Added Carbon Icons to FidesUI [#5416](https://github.com/ethyca/fides/pull/5416)
- Apply new color palette as scss module [#5453](https://github.com/ethyca/fides/pull/5453)
- Fixing external SaaS connector tests [#5463](https://github.com/ethyca/fides/pull/5463)
- Updating Paramiko to version 3.4.1 to prevent warning during server startup [#5467](https://github.com/ethyca/fides/pull/5467)

## [2.48.2](https://github.com/ethyca/fides/compare/2.48.1...2.48.2)

### Fixed
- Fixed ValidationError for datasets with a connection_type [#5447](https://github.com/ethyca/fides/pull/5447)

## [2.48.1](https://github.com/ethyca/fides/compare/2.48.0...2.48.1)

### Fixed
 - API router sanitizer being too aggressive with NextJS Catch-all Segments [#5438](https://github.com/ethyca/fides/pull/5438)
 - Fix rendering of subfield names in D&D tables [#5439](https://github.com/ethyca/fides/pull/5439)
 - Fix BigQuery `partitioning` queries to properly support multiple identity clauses [#5432](https://github.com/ethyca/fides/pull/5432)

## [2.48.0](https://github.com/ethyca/fides/compare/2.47.1...2.48.0)

### Added
- Added Azure as an SSO provider. [#5402](https://github.com/ethyca/fides/pull/5402)
- Added endpoint to get privacy request access results urls [#5379](https://github.com/ethyca/fides/pull/5379)
- Added `connection_type` key in the `namespace` attribute of a Dataset's `fides_meta` [#5387](https://github.com/ethyca/fides/pull/5387)
- Added new RDS Postgres Connector [#5380](https://github.com/ethyca/fides/pull/5380)
- Added ability to customize column names in the Data Map report [#5400](https://github.com/ethyca/fides/pull/5400)
- Added Experience Config docs to the FidesJS documentation [#5405](https://github.com/ethyca/fides/pull/5405)
- Added UI for downloading privacy request access results [#5407](https://github.com/ethyca/fides/pull/5407)

### Fixed
- Fixed a bug where D&D tables were rendering stale data [#5372](https://github.com/ethyca/fides/pull/5372)
- Fixed issue where multiple login redirects could end up losing login return path [#5389](https://github.com/ethyca/fides/pull/5389)
- Fixed issue where Dataset with nested fields was unable to edit Categories [#5383](https://github.com/ethyca/fides/pull/5383)
- Fixed a visual bug where the "download" icon was off-center in some buttons [#5409](https://github.com/ethyca/fides/pull/5409)
- Fixed styling on "Dataset" field on system integration form [#5408](https://github.com/ethyca/fides/pull/5408)
- Fixed Snowflake DSR integration failing with syntax error [#5417](https://github.com/ethyca/fides/pull/5417)

### Changed
- The `Monitor` button trigger the same `confirmResourceMutation` (monitor, start classification) on muted parent resources as well as un-muted resources. Un-mute button for muted field resources which simply changes their status to `monitored`. [#5362](https://github.com/ethyca/fides/pull/5362)

### Developer Experience
- Fix warning messages from slowapi and docker [#5385](https://github.com/ethyca/fides/pull/5385)

## [2.47.1](https://github.com/ethyca/fides/compare/2.47.0...2.47.1)

### Added
- Adding access and erasure support for Gladly [#5346](https://github.com/ethyca/fides/pull/5346)
- Added icons for the Gladly, ShipStation, Microsoft Ads, and PowerReviews integrations [#5374](https://github.com/ethyca/fides/pull/5374)

### Changed
- Make the dbname in GoogleCloudSQLPostgresSchema optional [#5358](https://github.com/ethyca/fides/pull/5358)

### Fixed
- Fixed race condition where GPC being updated after FidesJS initialization caused Privacy Notices to be in the wrong state [#5384](https://github.com/ethyca/fides/pull/5384)
- Fixed issue where Dataset with nested fields was unable to edit Categories [#5383](https://github.com/ethyca/fides/pull/5383)
- Fixed button styling issues [#5386](https://github.com/ethyca/fides/pull/5386)
- Allow Responsys and Firebase connectors to ignore extra identities [#5388](https://github.com/ethyca/fides/pull/5388)
- Fixed cookies not deleting on opt-out [#5338](https://github.com/ethyca/fides/pull/5338)

## [2.47.0](https://github.com/ethyca/fides/compare/2.46.2...2.47.0)

### Added
- Make all "Description" table columns expandable in Admin UI tables [#5340](https://github.com/ethyca/fides/pull/5340)
- Added access support for Shipstation [#5343](https://github.com/ethyca/fides/pull/5343)
- Introduce custom reports to Data map report [#5352](https://github.com/ethyca/fides/pull/5352)
- Added models to support custom reports (Fidesplus) [#5344](https://github.com/ethyca/fides/pull/5344)

### Changed
- Updated the filter postprocessor (SaaS integration framework) to support dataset references [#5343](https://github.com/ethyca/fides/pull/5343)

### Developer Experience
- Migrate toggle switches from Chakra to Ant Design [#5323](https://github.com/ethyca/fides/pull/5323)
- Migrate buttons from Chakra to Ant Design [#5357](https://github.com/ethyca/fides/pull/5357)
- Replace `debugLog` with global scoped `fidesDebugger` for better debug experience and optimization of prod code [#5335](https://github.com/ethyca/fides/pull/5335)

### Fixed
- Updating the hash migration status check query to use the available indexes [#5336](https://github.com/ethyca/fides/pull/5336)
- Fixed column resize jank on all tables in Admin UI [#5340](https://github.com/ethyca/fides/pull/5340)
- Better handling of empty storage secrets in aws_util [#5347](https://github.com/ethyca/fides/pull/5347)
- Fix SSO Provider form saving when clicking the cancel button with a fully filled form [#5365](https://github.com/ethyca/fides/pull/5365)
- Fix bleedover of Data Categories into next column on Data map reporting [#5369](https://github.com/ethyca/fides/pull/5369)

### Removed
- Removing Adobe Campaign integration [#5364](https://github.com/ethyca/fides/pull/5364)

## [2.46.2](https://github.com/ethyca/fides/compare/2.46.1...2.46.2)

### Added
- Initial support for DSR requests against partitioned BigQuery tables [#5325](https://github.com/ethyca/fides/pull/5325)
- Added MySQL on RDS as a detection/discovery integration[#5275](https://github.com/ethyca/fides/pull/5275)
- Added new RDS MySQL Connector [#5343](https://github.com/ethyca/fides/pull/5343)

## [2.46.1](https://github.com/ethyca/fides/compare/2.46.0...2.46.1)

### Added
- Implement Soft Delete for PrivacyRequests [#5321](https://github.com/ethyca/fides/pull/5321/files)

### Removed
- Removing Shippo integration [#5349](https://github.com/ethyca/fides/pull/5349)

### Fixed
- Updated Attentive DSR integration [#5319](https://github.com/ethyca/fides/pull/5319)

## [2.46.0](https://github.com/ethyca/fides/compare/2.45.2...2.46.0)

### Fixed
- Ignore `400` errors from Talkable's `person` endpoint. [#5317](https://github.com/ethyca/fides/pull/5317)
- Fix Email Connector logs so they use configuration key instead of name [#5286](https://github.com/ethyca/fides/pull/5286)
- Updated Responsys and Firebase Auth integrations to allow multiple identities [#5318](https://github.com/ethyca/fides/pull/5318)
- Updated Shopify dataset in order to flag country, province, and other location values as read-only [#5282](https://github.com/ethyca/fides/pull/5282)
- Fix issues with cached or `window.fides_overrides` languages in the Minimal TCF banner [#5306](https://github.com/ethyca/fides/pull/5306)
- Fix issue with fides-js where the experience was incorrectly initialized as an empty object which appeared valid, when `undefined` was expected [#5309](https://github.com/ethyca/fides/pull/5309)
- Fix issue where newly added languages in Admin-UI were not being rendered in the preview [#5316](https://github.com/ethyca/fides/pull/5316)
- Fix bug where consent automation accordion shows for integrations that don't support consent automation [#5330](https://github.com/ethyca/fides/pull/5330)
- Fix issue where custom overrides (title, description, privacy policy url, etc.) were not being applied to the full TCF overlay [#5333](https://github.com/ethyca/fides/pull/5333)


### Added
- Added support for hierarchical notices in Privacy Center [#5291](https://github.com/ethyca/fides/pull/5291)
- Support row-level deletes for BigQuery and add erase_after support for database connectors [#5293](https://github.com/ethyca/fides/pull/5293)
- Added PUT endpoint for dataset configs [#5324](https://github.com/ethyca/fides/pull/5324)
- Namespace support for the BigQuery integration and datasets [#5294](https://github.com/ethyca/fides/pull/5294)
- Added ability to select multiple datasets on integrations in system integration view [#5327](https://github.com/ethyca/fides/pull/5327)
- Updated Fides.shopify() integration for Shopify Plus Consent [#5329](https://github.com/ethyca/fides/pull/5329)

### Changed
- Updated privacy notices to support notice hierarchies [#5272](https://github.com/ethyca/fides/pull/5272)
- Defaulting SecuritySettings.env to prod [#5326](https://github.com/ethyca/fides/pull/5326)

### Developer Experience
- Initialized Ant Design and Tailwindcss in Admin-UI to prepare for Design System migration [#5308](https://github.com/ethyca/fides/pull/5308)

## [2.45.2](https://github.com/ethyca/fides/compare/2.45.1...2.45.2)

### Fixed
- Updated the hash migration script to only run on tables with less than 1 million rows. [#5310](https://github.com/ethyca/fides/pull/5310)

## [2.45.1](https://github.com/ethyca/fides/compare/2.45.0...2.45.1)

### Added
- Support minimal GVL in minimal TCF response allowing Accept/Reject from banner before full GVL is loaded [#5298](https://github.com/ethyca/fides/pull/5298)

### Fixed
- Fixed discovery pagination [#5304](https://github.com/ethyca/fides/pull/5304)
- Fixed fides-no-scroll so it works in all browsers [#5299](https://github.com/ethyca/fides/pull/5299)

## [2.45.0](https://github.com/ethyca/fides/compare/2.44.0...2.45.0)

### Added
- Adding erasure support for PowerReviews [#5258](https://github.com/ethyca/fides/pull/5258)
- Adding erasure support for Attentive [#5258](https://github.com/ethyca/fides/pull/5261)
- Added a scheduled job to incrementally migrate from bcrypt hashes to SHA-256 hashes for stored identity values [#5256](https://github.com/ethyca/fides/pull/5256)
- Added the new Dynamic Erasure Email integrations [#5226](https://github.com/ethyca/fides/pull/5226)
- Add ability to edit dataset YAML from dataset view [#5262](https://github.com/ethyca/fides/pull/5262)
- Added support for "in progress" status in classification [#5248](https://github.com/ethyca/fides/pull/5248)
- Clarify GCP service account permissions when setting up Google Cloud SQL for Postgres in Admin-UI [#5245](https://github.com/ethyca/fides/pull/5266)
- Add onFidesEvent method for an alternative way to subscribe to Fides events [#5297](https://github.com/ethyca/fides/pull/5297)

### Changed
- Validate no path in `server_host` var for CLI config; if there is one then take only up until the first forward slash
- Update the Datamap report's Data categories column to support better expand/collapse behavior [#5265](https://github.com/ethyca/fides/pull/5265)
- Rename/refactor Privacy Notice Properties to support performance improvements [#5259](https://github.com/ethyca/fides/pull/5259)
- Improved logging and error visibility for TraversalErrors [#5263](https://github.com/ethyca/fides/pull/5263)

### Developer Experience
- Added performance mark timings to debug logs for fides.js [#5245](https://github.com/ethyca/fides/pull/5245)

### Fixed
- Fix wording in tooltip for Yotpo Reviews [#5274](https://github.com/ethyca/fides/pull/5274)
- Hardcode ConnectionConfigurationResponse.secrets [#5283](https://github.com/ethyca/fides/pull/5283)
- Fix Fides.shouldShouldShowExperience() to return false for modal-only experiences [#5281](https://github.com/ethyca/fides/pull/5281)

## [2.44.0](https://github.com/ethyca/fides/compare/2.43.1...2.44.0)

### Added
- Added Gzip Middleware for responses [#5225](https://github.com/ethyca/fides/pull/5225)
- Adding source and submitted_by fields to privacy requests (Fidesplus) [#5206](https://github.com/ethyca/fides/pull/5206)
- Added Action Required / Monitored / Unmonitored tabs to Data Detection & Discovery page [#5236](https://github.com/ethyca/fides/pull/5236)
- Adding erasure support for Microsoft Advertising [#5197](https://github.com/ethyca/fides/pull/5197)
- Implements fuzzy search for identities in Admin-UI Request Manager [#5232](https://github.com/ethyca/fides/pull/5232)
- New purpose header field for TCF banner [#5246](https://github.com/ethyca/fides/pull/5246)
- `fides` subcommand `pull` has resource name subcommands that take a `fides_key` argument allowing you to pull only one resource by name and type [#5260](https://github.com/ethyca/fides/pull/5260)

### Changed
- Removed unused `username` parameter from the Delighted integration configuration [#5220](https://github.com/ethyca/fides/pull/5220)
- Removed unused `ad_account_id` parameter from the Snap integration configuration [#5229](https://github.com/ethyca/fides/pull/5220)
- Updates to support consent signal processing (Fidesplus) [#5200](https://github.com/ethyca/fides/pull/5200)
- TCF Optimized for performance on initial load by offsetting most experience data until after banner is shown [#5230](https://github.com/ethyca/fides/pull/5230)
- Updates to support DynamoDB schema with Tokenless IAM auth [#5240](https://github.com/ethyca/fides/pull/5240)

### Developer Experience
- Sourcemaps are now working for fides-js in debug mode [#5222](https://github.com/ethyca/fides/pull/5222)

### Fixed
- Fix bug where Data Detection & Discovery table pagination fails to reset after navigating or searching  [#5234](https://github.com/ethyca/fides/pull/5234)
- Ignoring HTTP 400 error responses from the unsubscribe endpoint for HubSpot [#5237](https://github.com/ethyca/fides/pull/5237)
- Fix all `fides` API subcommands (`push`, `user`, etc) failing with an invalid server even when only passing `--help` [#5243](https://github.com/ethyca/fides/pull/5243)
- Fix bug where empty datasets / table wouldn't show a Monitor button  [#5249](https://github.com/ethyca/fides/pull/5249)

### Security
- Reduced timing differences in login endpoint [CVE-2024-45052](https://github.com/ethyca/fides/security/advisories/GHSA-2h46-8gf5-fmxv)
- Removed Jinja2 for email templates, the variables syntax changed from `{{variable_name}}` to `__VARIABLE_NAME__` [CVE-2024-45053](https://github.com/ethyca/fides/security/advisories/GHSA-c34r-238x-f7qx)


## [2.43.1](https://github.com/ethyca/fides/compare/2.43.0...2.43.1)

### Added
- Pydantic v1 -> Pydantic v2 upgrade [#5020](https://github.com/ethyca/fides/pull/5020)
- Added success toast on muting/ignoring resources in D&D tables [#5214](https://github.com/ethyca/fides/pull/5214)
- Added "data type" column to fields and subfields on D&D tables [#5218](https://github.com/ethyca/fides/pull/5218)
- Added support for navigating and editing nested fields in the Datasets page [#5216](https://github.com/ethyca/fides/pull/5216)

### Fixed
- Ignore `404` errors on Oracle Responsys deletions [#5203](https://github.com/ethyca/fides/pull/5203)
- Fix white screen issue when privacy request has null value for daysLeft [#5213](https://github.com/ethyca/fides/pull/5213)

### Changed
- Visual updates to badges in D&D result tables [#5212](https://github.com/ethyca/fides/pull/5212)
- Tweaked behavior of loading state on D&D table actions buttons [#5201](https://github.com/ethyca/fides/pull/5201)


## [2.43.0](https://github.com/ethyca/fides/compare/2.42.1...2.43.0)

### Added
- Added support for mapping a system's integration's consentable items to privacy notices [#5156](https://github.com/ethyca/fides/pull/5156)
- Added support for SSO Login with multiple providers (Fides Plus feature) [#5134](https://github.com/ethyca/fides/pull/5134)
- Adds user_read scope to approver role so that they can update their own password [#5178](https://github.com/ethyca/fides/pull/5178)
- Added PATCH endpoint for partially updating connection secrets [#5172](https://github.com/ethyca/fides/pull/5172)
- Add success toast on confirming classification in data discovery tables [#5182](https://github.com/ethyca/fides/pull/5182)
- Add function to return list of StagedResource objs according to list of URNs [#5192](https://github.com/ethyca/fides/pull/5192)
- Add DSR Support for ScyllaDB [#5140](https://github.com/ethyca/fides/pull/5140)
- Added support for nested fields in BigQuery in D&D result views [#5175](https://github.com/ethyca/fides/pull/5175)
- Added support for Vendor Count in Fides-JS overlay descriptions [#5210](https://github.com/ethyca/fides/pull/5210)

### Fixed
- Fixed the OAuth2 configuration for the Snap integration [#5158](https://github.com/ethyca/fides/pull/5158)
- Fixes a Marigold Sailthru error when a user does not exist [#5145](https://github.com/ethyca/fides/pull/5145)
- Fixed malformed HTML issue on switch components [#5166](https://github.com/ethyca/fides/pull/5166)
- Edit integration modal no longer requires reentering credentials when doing partial edits [#2436](https://github.com/ethyca/fides/pull/2436)
- Fixed a timing issue with tcf/gpp locator iframe naming [#5173](https://github.com/ethyca/fides/pull/5173)
- Detection & Discovery: The when column will now display the correct value with a tooltip showing the full date and time [#5177](https://github.com/ethyca/fides/pull/5177)
- Fixed minor issues with the SSO providers form [#5183](https://github.com/ethyca/fides/pull/5183)

### Changed
- Removed PRIVACY_REQUEST_READ scope from Viewer role [#5184](https://github.com/ethyca/fides/pull/5184)
- Asynchronously load GVL translations in FidesJS instead of blocking UI rendering [#5187](https://github.com/ethyca/fides/pull/5187)
- Model changes to support consent signals (Fidesplus) [#5190](https://github.com/ethyca/fides/pull/5190)
- Updated Datasets page with new UI for better usability and consistency with Detection and Discovery UI [#5191](https://github.com/ethyca/fides/pull/5191)
- Updated the Yotpo Reviews integration to use email and phone number identities instead of external ID [#5169](https://github.com/ethyca/fides/pull/5169)
- Update TCF banner button layout and styles [#5204](https://github.com/ethyca/fides/pull/5204)


### Developer Experience
- Fixes some ESLint configuration issues [#5176](https://github.com/ethyca/fides/pull/5176)

## [2.42.1](https://github.com/ethyca/fides/compare/2.42.0...2.42.1)

### Fixed
- Fixed language picker cut-off in mobile on CMP banner and modal [#5159](https://github.com/ethyca/fides/pull/5159)
- Fixed button sizes on CMP modal [#5161](https://github.com/ethyca/fides/pull/5161)

## [2.42.0](https://github.com/ethyca/fides/compare/2.41.0...2.42.0)

### Added
- Add AWS Tags in the meta field for Fides system when using `fides generate` [#4998](https://github.com/ethyca/fides/pull/4998)
- Added access and erasure support for Checkr integration [#5121](https://github.com/ethyca/fides/pull/5121)
- Added support for special characters in SaaS request payloads [#5099](https://github.com/ethyca/fides/pull/5099)
- Added support for displaying notices served in the Consent Banner [#5125](https://github.com/ethyca/fides/pull/5125)
- Added ability to choose whether to use Opt In/Out buttons or Acknowledge button in the Consent Banner [#5125](https://github.com/ethyca/fides/pull/5125)
- Add "status" field to detection & discovery tables [#5141](https://github.com/ethyca/fides/pull/5141)
- Added optional filters `exclude_saas_datasets` and `only_unlinked_datasets` to the list datasets endpoint [#5132](https://github.com/ethyca/fides/pull/5132)
- Add new config options to support notice-only banner and modal [#5136](https://github.com/ethyca/fides/pull/5136)
- Added models to support bidirectional consent (Fides Plus feature) [#5118](https://github.com/ethyca/fides/pull/5118)

### Changed
- Moving Privacy Center endpoint logging behind debug flag [#5103](https://github.com/ethyca/fides/pull/5103)
- Serve GVL languages as they are requested [#5112](https://github.com/ethyca/fides/pull/5112)
- Changed text on system integrations tab to direct to new integration management [#5097](https://github.com/ethyca/fides/pull/5097)
- Updates to consent experience styling [#5085](https://github.com/ethyca/fides/pull/5085)
- Updated the dataset page to display the new table and support pagination [#5130](https://github.com/ethyca/fides/pull/5130)
- Improve performance by removing the need to load every system into redux store [#5135](https://github.com/ethyca/fides/pull/5135)
- Use the `user_id` from a Segment Trait instead of an `email` when deleting a user in Segment [#5004](https://github.com/ethyca/fides/pull/5004)
- Moves some endpoints for property-specific messaging from OSS -> plus [#5069](https://github.com/ethyca/fides/pull/5069)
- Text changes in monitor config table and form [#5142](https://github.com/ethyca/fides/pull/5142)
- Improve API error messages when using is_default field on taxonomy resources [#5147](https://github.com/ethyca/fides/pull/5147)

### Developer Experience
- Add `.syncignore` to reduce file sync size with new volumes [#5104](https://github.com/ethyca/fides/pull/5104)
- Fix sourcemap generation in development version of FidesJS [#5119](https://github.com/ethyca/fides/pull/5119)
- Upgrade to Next.js v14 [#5111](https://github.com/ethyca/fides/pull/5111)
- Upgrade and consolidate linting and formatting tools [#5128](https://github.com/ethyca/fides/pull/5128)

### Fixed
- Resolved an issue pulling all blog authors for the Shopify integration [#5043](https://github.com/ethyca/fides/pull/5043)
- Fixed typo in the BigQuery integration description [#5120](https://github.com/ethyca/fides/pull/5120)
- Fixed default values of Experience config toggles [#5123](https://github.com/ethyca/fides/pull/5123)
- Skip indexing Custom Privacy Request Field array values [#5127](https://github.com/ethyca/fides/pull/5127)
- Fixed Admin UI issue where banner would disappear in Experience Preview with GPC enabled [#5131](https://github.com/ethyca/fides/pull/5131)
- Fixed not being able to edit a monitor from scheduled to not scheduled [#5114](https://github.com/ethyca/fides/pull/5114)
- Migrating missing Fideslang 2.0 data categories [#5073](https://github.com/ethyca/fides/pull/5073)
- Fixed wrong system count on Datamap page [#5151](https://github.com/ethyca/fides/pull/5151)
- Fixes some responsive styling issues in the consent banner on mobile sized screens [#5157](https://github.com/ethyca/fides/pull/5157)

## [2.41.0](https://github.com/ethyca/fides/compare/2.40.0...2.41.0)

### Added
- Added erasure support for Alchemer integration [#4925](https://github.com/ethyca/fides/pull/4925)
- Added new columns and action buttons to discovery monitors table [#5068](https://github.com/ethyca/fides/pull/5068)
- Added field to exclude databases on MonitorConfig [#5080](https://github.com/ethyca/fides/pull/5080)
- Added key pair authentication for the Snowflake integration [#5079](https://github.com/ethyca/fides/pull/5079)

### Changed
- Updated the sample dataset for the Amplitude integration [#5063](https://github.com/ethyca/fides/pull/5063)
- Updated System's page to display a table that uses a paginated endpoint [#5084](https://github.com/ethyca/fides/pull/5084)
- Messaging page now shows a notice if you have properties without any templates [#5077](https://github.com/ethyca/fides/pull/5077)
- Endpoints for listing systems (GET /system) and datasets (GET /dataset) now support optional pagination [#5071](https://github.com/ethyca/fides/pull/5071)
- Messaging page will now show a notice about using global mode [#5090](https://github.com/ethyca/fides/pull/5090)
- Changed behavior of project selection modal in discovery monitor form [#5092](https://github.com/ethyca/fides/pull/5092)
- Data category selector for Discovery results won't show disabled categories [#5102](https://github.com/ethyca/fides/pull/5102)

### Developer Experience
- Upgrade to React 18 and Chakra 2, including other dependencies [#5036](https://github.com/ethyca/fides/pull/5036)
- Added support for "output templates" in read SaaS requests [#5054](https://github.com/ethyca/fides/pull/5054)
- URL for deployment instructions when the webserver is running [#5088](https://github.com/ethyca/fides/pull/5088)
- Optimize TCF bundle with just-in-time GVL translations [#5074](https://github.com/ethyca/fides/pull/5074)
- Added `performance.mark()` to FidesJS events for performance testing. [#5105](https://github.com/ethyca/fides/pull/5105)

### Fixed
- Fixed bug with unescaped table names in mysql queries [#5072](https://github.com/ethyca/fides/pull/5072/)
- Fixed bug with unresponsive messaging ui [#5081](https://github.com/ethyca/fides/pull/5081/)
- Fixed FidesKey constructor bugs in CLI [#5113](https://github.com/ethyca/fides/pull/5113)


## [2.40.0](https://github.com/ethyca/fides/compare/2.39.2...2.40.0)

### Added
- Adds last_monitored and enabled attributes to MonitorConfig [#4991](https://github.com/ethyca/fides/pull/4991)
- New messaging page. Allows managing messaging templates for different properties. [#5005](https://github.com/ethyca/fides/pull/5005)
- Ability to configure "Enforcement Level" for Privacy Notices [#5025](https://github.com/ethyca/fides/pull/5025)
- BE cleanup for property-specific messaging [#5006](https://github.com/ethyca/fides/pull/5006)
- If property_id param was used, store it as part of the consent request [#4915](https://github.com/ethyca/fides/pull/4915)
- Invite users via email flow [#4539](https://github.com/ethyca/fides/pull/4539)
- Added new Google Cloud SQL for Postgres Connector [#5014](https://github.com/ethyca/fides/pull/5014)
- Added access and erasure support for the Twilio SMS integration [#4979](https://github.com/ethyca/fides/pull/4979)
- Added erasure support for Snap integration [#5011](https://github.com/ethyca/fides/pull/5011)

### Changed
- Navigation changes. 'Management' was renamed 'Settings'. Properties was moved to Settings section. [#5005](https://github.com/ethyca/fides/pull/5005)
- Changed discovery monitor form behavior around execution date/time selection [#5017](https://github.com/ethyca/fides/pull/5017)
- Changed integration form behavior when errors occur [#5023](https://github.com/ethyca/fides/pull/5023)
- Replaces typescript-cookie with js-cookie [#5022](https://github.com/ethyca/fides/pull/5022)
- Updated pymongo version to 4.7.3 [#5019](https://github.com/ethyca/fides/pull/5019)
- Upgraded Datamap instance of `react-table` to v8 [#5024](https://github.com/ethyca/fides/pull/5024)
- Updated create privacy request modal from admin-ui to include all custom fields  [#5029](https://github.com/ethyca/fides/pull/5029)
- Update name of Ingress/Egress columns in Datamap Report to Sources/Destinations [#5045](https://github.com/ethyca/fides/pull/5045)
- Datamap report now includes a 'cookies' column [#5052](https://github.com/ethyca/fides/pull/5052)
- Changed behavior of project selection UI in discovery monitor form [#5049](https://github.com/ethyca/fides/pull/5049)
- Updating DSR filtering to use collection-level data categories [#4999](https://github.com/ethyca/fides/pull/4999)
- Changed discovery monitor form to skip project selection UI when no projects exist [#5056](https://github.com/ethyca/fides/pull/5056)

### Fixed
- Fixed intermittent connection issues with Redshift by increasing timeout and preferring SSL in test connections [#4981](https://github.com/ethyca/fides/pull/4981)
- Fixed data detection & discovery results not displaying correctly across multiple pages[#5060](https://github.com/ethyca/fides/pull/5060)

### Developer Experience
- Fixed various environmental issues when running Cypress tests locally [#5040](https://github.com/ethyca/fides/pull/5040)

## [2.39.2](https://github.com/ethyca/fides/compare/2.39.1...2.39.2)

### Fixed
- Restrict Delete Systems API endpoint such that user must have "SYSTEM_DELETE" scope [#5037](https://github.com/ethyca/fides/pull/5037)

### Security
- Remove the SERVER_SIDE_FIDES_API_URL env variable from the client clientSettings [CVE-2024-31223](https://github.com/ethyca/fides/security/advisories/GHSA-53q7-4874-24qg)

## [2.39.1](https://github.com/ethyca/fides/compare/2.39.0...2.39.1)

### Fixed
- Fixed a bug where system information form was not loading for Viewer users [#5034](https://github.com/ethyca/fides/pull/5034)
- Fixed viewers being given the option to delete systems [#5035](https://github.com/ethyca/fides/pull/5035)
- Restrict Delete Systems API endpoint such that user must have "SYSTEM_DELETE" scope [#5037](https://github.com/ethyca/fides/pull/5037)

### Removed
- Removed the `fetch` polyfill from FidesJS [#5026](https://github.com/ethyca/fides/pull/5026)

### Security
- Removed FidesJS's exposure to `polyfill.io` supply chain attack [CVE-2024-38537](https://github.com/ethyca/fides/security/advisories/GHSA-cvw4-c69g-7v7m)

## [2.39.0](https://github.com/ethyca/fides/compare/2.38.1...2.39.0)

### Added
- Adds the start of the Scylla DB Integration [#4946](https://github.com/ethyca/fides/pull/4946)
- Added model and data migrations and CRUD-layer operations for property-specific messaging [#4901](https://github.com/ethyca/fides/pull/4901)
- Added option in FidesJS SDK to only disable notice-served API [#4965](https://github.com/ethyca/fides/pull/4965)
- External ID support for consent management [#4927](https://github.com/ethyca/fides/pull/4927)
- Added access and erasure support for the Greenhouse Harvest integration [#4945](https://github.com/ethyca/fides/pull/4945)
- Add an S3 connection type (currently used for discovery and detection only) [#4930](https://github.com/ethyca/fides/pull/4930)
- Support for Limited FIDES__CELERY__* Env Vars [#4980](https://github.com/ethyca/fides/pull/4980)
- Implement sending emails via property-specific messaging templates [#4950](https://github.com/ethyca/fides/pull/4950)
- New privacy request search to replace existing endpoint [#4987](https://github.com/ethyca/fides/pull/4987)
- Added new Google Cloud SQL for MySQL Connector [#4949](https://github.com/ethyca/fides/pull/4949)
- Add new options for integrations for discovery & detection [#5000](https://github.com/ethyca/fides/pull/5000)
- Add new `FidesInitializing` event for when FidesJS begins initialization [#5010](https://github.com/ethyca/fides/pull/5010)

### Changed
- Move new data map reporting table out of beta and remove old table from Data Lineage map. [#4963](https://github.com/ethyca/fides/pull/4963)
- Disable the 'connect to a database' button if the `dataDiscoveryAndDetection` feature flag is enabled [#1455](https://github.com/ethyca/fidesplus/pull/1455)
- Upgrade Privacy Request table to use FidesTable V2 [#4990](https://github.com/ethyca/fides/pull/4990)
- Add copy to project selection modal and tweak copy on discovery monitors table [#5007](https://github.com/ethyca/fides/pull/5007)

### Fixed
- Fixed an issue where the GPP signal status was prematurely set to `ready` in some scenarios [#4957](https://github.com/ethyca/fides/pull/4957)
- Removed exteraneous `/` from the several endpoint URLs [#4962](https://github.com/ethyca/fides/pull/4962)
- Fixed and optimized Database Icon SVGs used in Datamap [#4969](https://github.com/ethyca/fides/pull/4969)
- Masked "Keyfile credentials" input on integration config form [#4971](https://github.com/ethyca/fides/pull/4971)
- Fixed validations for privacy declaration taxonomy labels when creating/updating a System [#4982](https://github.com/ethyca/fides/pull/4982)
- Allow property-specific messaging to work with non-custom templates [#4986](https://github.com/ethyca/fides/pull/4986)
- Fixed an issue where config object was being passed twice to `fides.js` output [#5010](https://github.com/ethyca/fides/pull/5010)
- Disabling Fides initialization now also disables GPP initialization [#5010](https://github.com/ethyca/fides/pull/5010)
- Fixes Vendor table formatting [#5013](https://github.com/ethyca/fides/pull/5013)

## [2.38.1](https://github.com/ethyca/fides/compare/2.38.0...2.38.1)

### Changed
- Disable the 'connect to a database' button if the `dataDiscoveryAndDetection` feature flag is enabled [#4972](https://github.com/ethyca/fidesplus/pull/4972)
- Oracle Responsys: Include Profile Extension Tables in DSRs[#4937](https://github.com/ethyca/fides/pull/4937)

### Fixed
- Fixed "add" icons on some buttons being wrong size [#4975](https://github.com/ethyca/fides/pull/4975)
- Fixed ability to update consent preferences after they've previously been set [#4984](https://github.com/ethyca/fides/pull/4984)

## [2.38.0](https://github.com/ethyca/fides/compare/2.37.0...2.38.0)

### Added
- Deprecate LastServedNotice (lastservednoticev2) table [#4910](https://github.com/ethyca/fides/pull/4910)
- Added erasure support to the Recurly integration [#4891](https://github.com/ethyca/fides/pull/4891)
- Added UI for configuring integrations for detection/discovery [#4922](https://github.com/ethyca/fides/pull/4922)
- New queue for saving privacy preferences/notices served [#4931](https://github.com/ethyca/fides/pull/4931)
- Expose number of tasks in queue in worker health check [#4931](https://github.com/ethyca/fides/pull/4931)
- Track when preferences/notices served received [#4931](https://github.com/ethyca/fides/pull/4931)
- Request overrides for opt-in and opt-out consent requests [#4920](https://github.com/ethyca/fides/pull/4920)
- Added query_param_key to Privacy Center schema [#4939](https://github.com/ethyca/fides/pull/4939)
- Fill custom privacy request fields with query_param_key [#4948](https://github.com/ethyca/fides/pull/4948)
- Add `datasource_params` column to MonitorConfig DB model [#4951](https://github.com/ethyca/fides/pull/4951)
- Added ability to open system preview side panel from new data map table [#4944](https://github.com/ethyca/fides/pull/4944)
- Added success toast message after monitoring a resource [#4958](https://github.com/ethyca/fides/pull/4958)
- Added UI for displaying, adding and editing discovery monitors [#4954](https://github.com/ethyca/fides/pull/4954)

### Changed
- Set default ports for local development of client projects (:3001 for privacy center and :3000 for admin-ui) [#4912](https://github.com/ethyca/fides/pull/4912)
- Update privacy center port to :3001 for nox [#4918](https://github.com/ethyca/fides/pull/4918)
- Optimize speed by generating the uuids in the client side for consent requests [#4933](https://github.com/ethyca/fides/pull/4933)
- Update Privacy Center toast text for consistent capitalization [#4936](https://github.com/ethyca/fides/pull/4936)
- Update Custom Fields table and Domain Verification table to use FidesTable V2. Remove V1 components. [#4932](https://github.com/ethyca/fides/pull/4932)
- Updated how Fields are generated for DynamoDB, improved error handling [#4943](https://github.com/ethyca/fides/pull/4943)

### Fixed
- Fixed an issue where the test integration action failed for the Zendesk integration [#4929](https://github.com/ethyca/fides/pull/4929)
- Fixed an issue where language form field error message was not displaying properly [#4942](https://github.com/ethyca/fides/pull/4942)
- Fixed an issue where the consent cookie could not be set on multi-level root domain (e.g. co.uk, co.jp) [#4935](https://github.com/ethyca/fides/pull/4935)
- Fixed an issue where the unique device ID was not being retained when Fides.js was reinitialized [#4947](https://github.com/ethyca/fides/pull/4947)
- Fixed inconsistent font sizes on new integrations UI [#4959](https://github.com/ethyca/fides/pull/4959)

## [2.37.0](https://github.com/ethyca/fides/compare/2.36.0...2.37.0)

### Added
- Added initial version for Helios: Data Discovery and Detection [#4839](https://github.com/ethyca/fides/pull/4839)
- Added shouldShowExperience to the Fides global and FidesInitialized events [#4895](https://github.com/ethyca/fides/pull/4895)
- Enhancements to `MonitorConfig` DB model to support new functionality [#4888](https://github.com/ethyca/fides/pull/4888)
- Added developer option to disable auto-initialization on FidesJS bundles. [#4900](https://github.com/ethyca/fides/pull/4900)
- Adding property ID to served notice history and privacy preference history [#4886](https://github.com/ethyca/fides/pull/4886)
- Adding privacy_center_config and stylesheet fields to the Property model [#4879](https://github.com/ethyca/fides/pull/4879)
- Adds generic async callback integration support [#4865](https://github.com/ethyca/fides/pull/4865)
- Ability to `downgrade` the application DB through the `/admin/db` endpoint [#4893](https://github.com/ethyca/fides/pull/4893)
- Added support for custom property paths, configs and stylesheets for privacy center [#4907](https://github.com/ethyca/fides/pull/4907)
- Include the scopes required for a given action in `403` response when client does not have sufficient permissions [#4905](https://github.com/ethyca/fides/pull/4905)

### Changed
- Rename MinimalPrivacyExperience class and usages [#4889](https://github.com/ethyca/fides/pull/4889)
- Included fidesui as part of the monorepo [#4880](https://github.com/ethyca/fides/pull/4880)
- Improve `geolocation` and `property_id` error response to return 400 status instead of 500 server error on /fides.js endpoint [#4884](https://github.com/ethyca/fides/pull/4884)
- Fixing middleware logging in Fides.js to remove incorrect status codes and durations [#4885](https://github.com/ethyca/fides/pull/4885)
- Improve load performance and DOM monitoring for FidesJS [#4896](https://github.com/ethyca/fides/pull/4896)

### Fixed
- Fixed an issue with the Iterate connector returning at least one param_value references an invalid field for the 'update' request of user [#4528](https://github.com/ethyca/fides/pull/4528)
- Enhanced classification of the dataset used with Twilio [#4872](https://github.com/ethyca/fides/pull/4872)
- Reduce privacy center logging to not show response size limit when the /fides.js endpoint has a size bigger than 4MB [#4878](https://github.com/ethyca/fides/pull/4878)
- Fixed an issue where sourcemaps references were unintentionally included in the FidesJS bundle [#4887](https://github.com/ethyca/fides/pull/4887)
- Handle a 404 response from Segment when a user ID or email is not found [#4902](https://github.com/ethyca/fides/pull/4902)
- Fixed TCF styling issues [#4904](https://github.com/ethyca/fides/pull/4904)
- Fixed an issue where the Trigger Modal Link was not being populated correctly in the translation form [#4911](https://github.com/ethyca/fides/pull/4911)

### Security
- Escape SQLAlchemy passwords [CVE-2024-34715](https://github.com/ethyca/fides/security/advisories/GHSA-8cm5-jfj2-26q7)
- Properly mask nested BigQuery secrets in connection configuration endpoints [CVE-2024-35189](https://github.com/ethyca/fides/security/advisories/GHSA-rcvg-jj3g-rj7c)

## [2.36.0](https://github.com/ethyca/fides/compare/2.35.1...2.36.0)

### Added
- Added multiple language translations support for privacy center consent page [#4785](https://github.com/ethyca/fides/pull/4785)
- Added ability to export the contents of datamap report [#1545](https://github.com/ethyca.atlassian.net/browse/PROD-1545)
- Added `System` model support for new `vendor_deleted_date` field on Compass vendor records [#4818](https://github.com/ethyca/fides/pull/4818)
- Added custom JSON (de)serialization to shared DB engines to handle non-standard data types in JSONB columns [#4818](https://github.com/ethyca/fides/pull/4818)
- Added state persistence across sessions to the datamap report table [#4853](https://github.com/ethyca/fides/pull/4853)
- Removed currentprivacypreference and lastservednotice tables [#4846](https://github.com/ethyca/fides/pull/4846)
- Added initial version for Helios: Data Discovery and Detection [#4839](https://github.com/ethyca/fides/pull/4839)
- Adds new var to track fides js overlay types [#4869](https://github.com/ethyca/fides/pull/4869)

### Changed
- Changed filters on the data map report table to use checkbox collapsible tree view [#4864](https://github.com/ethyca/fides/pull/4864)

### Fixed
- Remove the extra 'white-space: normal' CSS for FidesJS HTML descriptions [#4850](https://github.com/ethyca/fides/pull/4850)
- Fixed data map report to display second level names from the taxonomy as primary (bold) label [#4856](https://github.com/ethyca/fides/pull/4856)
- Ignore invalid three-character country codes for FidesJS geolocation (e.g. "USA") [#4877](https://github.com/ethyca/fides/pull/4877)

### Developer Experience
- Update typedoc-plugin-markdown to 4.0.0 [#4870](https://github.com/ethyca/fides/pull/4870)

## [2.35.1](https://github.com/ethyca/fides/compare/2.35.0...2.35.1)

### Added
- Added access and erasure support for Marigold Engage by Sailthru integration [#4826](https://github.com/ethyca/fides/pull/4826)
- Update fides_disable_save_api option in FidesJS SDK to disable both privacy-preferences & notice-served APIs [#4860](https://github.com/ethyca/fides/pull/4860)

### Fixed
- Fixing issue where privacy requests not approved before upgrading to 2.34 couldn't be processed [#4855](https://github.com/ethyca/fides/pull/4855)
- Ensure only GVL vendors from Compass are labeled as such [#4857](https://github.com/ethyca/fides/pull/4857)
- Fix handling of some ISO-3166 geolocation edge cases in Privacy Center /fides.js endpoint [#4858](https://github.com/ethyca/fides/pull/4858)

### Changed
- Hydrates GTM datalayer to match supported FidesEvent Properties [#4847](https://github.com/ethyca/fides/pull/4847)
- Allows a SaaS integration request to process HTTP 204 No Content without erroring trying to unwrap the response. [#4834](https://github.com/ethyca/fides/pull/4834)
- Sets `sslmode` to prefer for Redshift connections when generating datasets [#4849](https://github.com/ethyca/fides/pull/4849)
- Included searching by `email` for the Segment integration [#4851](https://github.com/ethyca/fides/pull/4851)

## [2.35.0](https://github.com/ethyca/fides/compare/2.34.0...2.35.0)
