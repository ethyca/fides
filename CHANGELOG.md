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

## [Unreleased](https://github.com/ethyca/fides/compare/2.52.0...main)

### Added
- Added Action Center MVP behind new feature flag [#5622](https://github.com/ethyca/fides/pull/5622)
- Added cache-clearing methods to the `DBCache` model to allow deleting cache entries [#5629](https://github.com/ethyca/fides/pull/5629)
- Adds partitioning, custom identities, multiple identities to test coverage for BigQuery Enterprise [#5618](https://github.com/ethyca/fides/pull/5618)
- Added Datahub groundwork required by Fidesplus [#5666](https://github.com/ethyca/fides/pull/5666)

### Changed
- Updated brand link url [#5656](https://github.com/ethyca/fides/pull/5656)
- Changed "Reclassify" D&D button to show in an overflow menu when row actions are overcrowded [#5655](https://github.com/ethyca/fides/pull/5655)
- Removed primary key requirements for BigQuery and Postgres erasures [#5591](https://github.com/ethyca/fides/pull/5591)
- Updated `DBCache` model so setting cache value always updates the updated_at field [#5669](https://github.com/ethyca/fides/pull/5669)

### Fixed
- Fixed issue where the custom report "reset" button was not working as expected [#5649](https://github.com/ethyca/fides/pull/5649)
- Fixed column ordering issue in the Data Map report [#5649](https://github.com/ethyca/fides/pull/5649)
- Fixed issue where the Data Map report filter dialog was missing an Accordion item label [#5649](https://github.com/ethyca/fides/pull/5649)

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
- Added ability to export the contents of datamap report [#1545](https://ethyca.atlassian.net/browse/PROD-1545)
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

### Added
- Added DSR 3.0 Scheduling which supports running DSR's in parallel with first-class request tasks [#4760](https://github.com/ethyca/fides/pull/4760)
- Added carets to collapsible sections in the overlay modal [#4793](https://github.com/ethyca/fides/pull/4793)
- Added erasure support for OpenWeb [#4735](https://github.com/ethyca/fides/pull/4735)
- Added support for configuration of pre-approval webhooks [#4795](https://github.com/ethyca/fides/pull/4795)
- Added fides_clear_cookie option to FidesJS SDK to load CMP without preferences on refresh [#4810](https://github.com/ethyca/fides/pull/4810)
- Added FidesUpdating event to FidesJS SDK [#4816](https://github.com/ethyca/fides/pull/4816)
- Added `reinitialize` method to FidesJS SDK [#4812](https://github.com/ethyca/fides/pull/4812)
- Added undeclared data category columns to data map report table [#4781](https://github.com/ethyca/fides/pull/4781)
- Fully implement pre-approval webhooks [#4822](https://github.com/ethyca/fides/pull/4822)
- Sync models and database for pre-approval webhooks [#4838](https://github.com/ethyca/fides/pull/4838)

### Changed
- Removed the Celery startup banner from the Fides worker logs [#4814](https://github.com/ethyca/fides/pull/4814)
- Improve performance of Snowflake schema generation [#4587](https://github.com/ethyca/fides/pull/4587)

### Fixed
- Fixed bug prevented adding new privacy center translations [#4786](https://github.com/ethyca/fides/pull/4786)
- Fixed bug where Privacy Policy links would be shown without a configured URL [#4801](https://github.com/ethyca/fides/pull/4801)
- Fixed bug prevented adding new privacy center translations [#4786](https://github.com/ethyca/fides/pull/4786)
- Fixed bug where Language selector button was overlapping other buttons when Privacy Policy wasn't present. [#4815](https://github.com/ethyca/fides/pull/4815)
- Fixed bug where icons of the Language selector were displayed too small on some sites [#4815](https://github.com/ethyca/fides/pull/4815)
- Fixed bug where GPP US National Section was incorrectly included when the State by State approach was selected [#4823]https://github.com/ethyca/fides/pull/4823
- Fixed DSR 3.0 Scheduling bug where Approved Privacy Requests that failed wouldn't change status [#4837](https://github.com/ethyca/fides/pull/4837)

## [2.34.0](https://github.com/ethyca/fides/compare/2.33.1...2.34.0)

### Added

- Added new field for modal trigger link translation [#4761](https://github.com/ethyca/fides/pull/4761)
- Added `getModalLinkLabel` method to global fides object [#4766](https://github.com/ethyca/fides/pull/4766)
- Added language switcher to fides overlay modal [#4773](https://github.com/ethyca/fides/pull/4773)
- Added modal link label to experience translation model [#4767](https://github.com/ethyca/fides/pull/4767)
- Added support for custom identities [#4764](https://github.com/ethyca/fides/pull/4764)
- Added developer option to force GPP API on FidesJS bundles [#4799](https://github.com/ethyca/fides/pull/4799)

### Changed

- Changed the Stripe integration for `Cards` to delete instead of update due to possible issues of a past expiration date [#4768](https://github.com/ethyca/fides/pull/4768)
- Changed display of Data Uses, Categories and Subjects to user friendly names in the Data map report [#4774](https://github.com/ethyca/fides/pull/4774)
- Update active disabled Fides.js toggle color to light grey [#4778](https://github.com/ethyca/fides/pull/4778)
- Update FidesJS fides_embed option to support embedding both banner & modal components [#4782](https://github.com/ethyca/fides/pull/4782)
- Add a few CSS classes to help with styling FidesJS button groups [#4789](https://github.com/ethyca/fides/pull/4789)
- Changed GPP extension to be pre-bundled in appropriate circumstances, as opposed to another fetch [#4780](https://github.com/ethyca/fides/pull/4780)

### Fixed

- Fixed select dropdowns being cut off by edges of modal forms [#4757](https://github.com/ethyca/fides/pull/4757)
- Changed "allow user to dismiss" toggle to show on config form for TCF experience [#4755](https://github.com/ethyca/fides/pull/4755)
- Fixed issue when loading the privacy request detail page [#4775](https://github.com/ethyca/fides/pull/4775)
- Fixed connection test for Aircall [#4756](https://github.com/ethyca/fides/pull/4756/pull)
- Fixed issues connecting to Redshift due to character encoding and SSL requirements [#4790](https://github.com/ethyca/fides/pull/4790)
- Fixed the way the name identity is handled in the Privacy Center [#4791](https://github.com/ethyca/fides/pull/4791)

### Developer Experience

- Build a `fides-types.d.ts` type declaration file to include alongside our FidesJS developer docs [#4772](https://github.com/ethyca/fides/pull/4772)

## [2.33.1](https://github.com/ethyca/fides/compare/2.33.0...2.33.1)

### Added

- Adds CUSTOM_OPTIONS_PATH to Privacy Center env vars [#4769](https://github.com/ethyca/fides/pull/4769)

## [2.33.0](https://github.com/ethyca/fides/compare/2.32.0...2.33.0)

### Added

- Added models for Privacy Center configuration (for plus users) [#4716](https://github.com/ethyca/fides/pull/4716)
- Added ability to delete properties [#4708](https://github.com/ethyca/fides/pull/4708)
- Add interface for submitting privacy requests in admin UI [#4738](https://github.com/ethyca/fides/pull/4738)
- Added language switching support to the FidesJS UI based on configured translations [#4737](https://github.com/ethyca/fides/pull/4737)
- Added ability to override some experience language and primary color [#4743](https://github.com/ethyca/fides/pull/4743)
- Generate FidesJS SDK Reference Docs from tsdoc comments [#4736](https://github.com/ethyca/fides/pull/4736)
- Added erasure support for Adyen [#4735](https://github.com/ethyca/fides/pull/4735)
- Added erasure support for Iterable [#4695](https://github.com/ethyca/fides/pull/4695)

### Changed

- Updated privacy notice & experience forms to hide translation UI when user doesn't have translation feature [#4728](https://github.com/ethyca/fides/pull/4728), [#4734](https://github.com/ethyca/fides/pull/4734)
- Custom privacy request fields now support list values [#4686](https://github.com/ethyca/fides/pull/4686)
- Update when GPP API reports signal status: ready [#4635](https://github.com/ethyca/fides/pull/4635)
- Update non-dismissable TCF and notice banners to show a black overlay and prevent scrolling [#4748](https://github.com/ethyca/fidesplus/pull/4748)
- Cleanup config vars for preview in Admin-UI [#4745](https://github.com/ethyca/fides/pull/4745)
- Show a "systems displayed" count on datamap map & table reporting page [#4752](https://github.com/ethyca/fides/pull/4752)
- Change default Canada Privacy Experience Config in migration to reference generic `ca` region [#4762](https://github.com/ethyca/fides/pull/4762)

### Fixed

- Fixed responsive issues with the buttons on the integration screen [#4729](https://github.com/ethyca/fides/pull/4729)
- Fixed hover/focus issues with the v2 tables [#4730](https://github.com/ethyca/fides/pull/4730)
- Disable editing of data use declaration name and type after creation [#4731](https://github.com/ethyca/fides/pull/4731)
- Cleaned up table borders [#4733](https://github.com/ethyca/fides/pull/4733)
- Initialization issues with ExperienceNotices (#4723)[https://github.com/ethyca/fides/pull/4723]
- Re-add CORS origin regex field to admin UI (#4742)[https://github.com/ethyca/fides/pull/4742]

### Developer Experience

- Added new script to allow recompiling of fides-js when the code changes [#4744](https://github.com/ethyca/fides/pull/4744)
- Update Cookie House to support for additional locations (Canada, Quebec, EEA) and a "property_id" override [#4750](https://github.com/ethyca/fides/pull/4750)

## [2.32.0](https://github.com/ethyca/fides/compare/2.31.1...2.32.0)

### Added

- Updated configuration pages for Experiences with live Preview of FidesJS banner & modal components [#4576](https://github.com/ethyca/fides/pull/4576)
- Added ability to configure multiple language translations for Notices & Experiences [#4576](https://github.com/ethyca/fides/pull/4576)
- Automatically localize all strings in FidesJS CMP UIs (banner, modal, and TCF overlay) based on user's locale and experience configuration [#4576](https://github.com/ethyca/fides/pull/4576)
- Added fides_locale option to override FidesJS locale detection [#4576](https://github.com/ethyca/fides/pull/4576)
- Update FidesJS to report notices served and preferences saved linked to the specific translations displayed [#4576](https://github.com/ethyca/fides/pull/4576)
- Added ability to prevent dismissal of FidesJS CMP UI via Experience configuration [#4576](https://github.com/ethyca/fides/pull/4576)
- Added ability to create & link Properties to support multiple Experiences in a single location [#4658](https://github.com/ethyca/fides/pull/4658)
- Added property_id query param to fides.js to filter experiences by Property when installed [#4676](https://github.com/ethyca/fides/pull/4676)
- Added Locations & Regulations pages to allow a wider selection of locations for consent [#4660](https://github.com/ethyca/fides/pull/4660)
- Erasure support for Simon Data [#4552](https://github.com/ethyca/fides/pull/4552)
- Added notice there will be no preview for Privacy Center types in the Experience preview [#4709](https://github.com/ethyca/fides/pull/4709)
- Removed properties beta flag [#4710](https://github.com/ethyca/fides/pull/4710)
- Add acknowledge button label to default Experience English form [#4714](https://github.com/ethyca/fides/pull/4714)
- Update FidesJS to support localizing CMP UI with configurable, non-English default locales [#4720](https://github.com/ethyca/fides/pull/4720)
- Add loading of template translations for notices and experiences [#4718](https://github.com/ethyca/fides/pull/4718)

### Changed

- Moved location-targeting from Notices to Experiences [#4576](https://github.com/ethyca/fides/pull/4576)
- Replaced previous default Notices & Experiences with new versions with updated locations, translations, etc. [#4576](https://github.com/ethyca/fides/pull/4576)
- Automatically migrate existing Notices & Experiences to updated model where possible [#4576](https://github.com/ethyca/fides/pull/4576)
- Replaced ability to configure banner "display configuration" to separate banner & modal components [#4576](https://github.com/ethyca/fides/pull/4576)
- Modify `fides user login` to not store plaintext password in `~/.fides-credentials` [#4661](https://github.com/ethyca/fides/pull/4661)
- Data model changes to support Notice and Experience-level translations [#4576](https://github.com/ethyca/fides/pull/4576)
- Data model changes to support Consent setup being Experience instead of Notice-driven [#4576](https://github.com/ethyca/fides/pull/4576)
- Build PrivacyNoticeRegion from locations and location groups [#4620](https://github.com/ethyca/fides/pull/4620)
- When saving locations, calculate and save location groups [#4620](https://github.com/ethyca/fides/pull/4620)
- Update privacy experiences page to use the new table component [#4652](https://github.com/ethyca/fides/pull/4652)
- Update privacy notices page to use the new table component [#4641](https://github.com/ethyca/fides/pull/4641)
- Bumped supported Python versions to `3.10.13`, `3.9.18`, and `3.8.18`. Bumped Debian base image from `-bullseye` to `-bookworm`. [#4630](https://github.com/ethyca/fides/pull/4630)
- Bumped Node.js base image from `16` to `20`. [#4684](https://github.com/ethyca/fides/pull/4684)

### Fixed

- Ignore 404 errors from Delighted and Kustomer when an erasure client is not found [#4593](https://github.com/ethyca/fides/pull/4593)
- Various FE fixes for Admin-UI experience config form [#4707](https://github.com/ethyca/fides/pull/4707)
- Fix modal preview in Admin-UI experience config form [#4712](https://github.com/ethyca/fides/pull/4712)
- Optimize FidesJS bundle size by only loading TCF static stings when needed [#4711](https://github.com/ethyca/fides/pull/4711)

## [2.31.0](https://github.com/ethyca/fides/compare/2.30.1...2.31.0)

### Added

- Add Great Britain as a consent option [#4628](https://github.com/ethyca/fides/pull/4628)
- Navbar update and new properties page [#4633](https://github.com/ethyca/fides/pull/4633)
- Access and erasure support for Oracle Responsys [#4618](https://github.com/ethyca/fides/pull/4618)

### Fixed

- Fix issue where "x" button on Fides.js components overwrites saved preferences [#4649](https://github.com/ethyca/fides/pull/4649)
- Initialize Fides.consent with default values from experience when saved consent cookie (fides_consent) does not exist [#4665](https://github.com/ethyca/fides/pull/4665)

### Changed

- Sets GPP applicableSections to -1 when a user visits from a state that is not part of the GPP [#4727](https://github.com/ethyca/fides/pull/4727)

## [2.30.1](https://github.com/ethyca/fides/compare/2.30.0...2.30.1)

### Fixed

- Configure logger correctly on worker initialization [#4624](https://github.com/ethyca/fides/pull/4624)

## [2.30.0](https://github.com/ethyca/fides/compare/2.29.0...2.30.0)

### Added

- Add enum and registry of supported languages [#4592](https://github.com/ethyca/fides/pull/4592)
- Access and erasure support for Talkable [#4589](https://github.com/ethyca/fides/pull/4589)
- Support temporary credentials in AWS generate + scan features [#4607](https://github.com/ethyca/fides/pull/4603), [#4608](https://github.com/ethyca/fides/pull/4608)
- Add ability to store and read Fides cookie in Base64 format [#4556](https://github.com/ethyca/fides/pull/4556)
- Structured logging for SaaS connector requests [#4594](https://github.com/ethyca/fides/pull/4594)
- Added Fides.showModal() to fides.js to allow programmatic opening of consent modals [#4617](https://github.com/ethyca/fides/pull/4617)

### Fixed

- Fixing issue when modifying Policies, Rules, or RuleTargets as a root user [#4582](https://github.com/ethyca/fides/pull/4582)

## [2.29.0](https://github.com/ethyca/fides/compare/2.28.0...2.29.0)

### Added

- View more modal to regulations page [#4574](https://github.com/ethyca/fides/pull/4574)
- Columns in data map reporting, adding multiple systems, and consent configuration tables can be resized. In the data map reporting table, fields with multiple values can show all or collapse all [#4569](https://github.com/ethyca/fides/pull/4569)
- Show custom fields in the data map report table [#4579](https://github.com/ethyca/fides/pull/4579)

### Changed

- Delay rendering the nav until all necessary queries are finished loading [#4571](https://github.com/ethyca/fides/pull/4571)
- Updating return value for crud.get_custom_fields_filtered [#4575](https://github.com/ethyca/fides/pull/4575)
- Updated user deletion confirmation flow to only require one confirmatory input [#4402](https://github.com/ethyca/fides/pull/4402)
- Moved `pymssl` to an optional dependency no longer installed by default with our python package [#4581](https://github.com/ethyca/fides/pull/4581)
- Fixed CORS domain update functionality [#4570](https://github.com/ethyca/fides/pull/4570)
- Update Domains page with ability to add/remove "organization" domains, view "administrator" domains set via security settings, and improve various UX bugs and copy [#4584](https://github.com/ethyca/fides/pull/4584)

### Fixed

- Fixed CORS domain update functionality [#4570](https://github.com/ethyca/fides/pull/4570)
- Completion emails are no longer attempted for consent requests [#4578](https://github.com/ethyca/fides/pull/4578)

## [2.28.0](https://github.com/ethyca/fides/compare/2.27.0...2.28.0)

### Added

- Erasure support for AppsFlyer [#4512](https://github.com/ethyca/fides/pull/4512)
- Datamap Reporting page [#4519](https://github.com/ethyca/fides/pull/4519)
- Consent support for Klaviyo [#4513](https://github.com/ethyca/fides/pull/4513)
- Form for configuring GPP settings [#4557](https://github.com/ethyca/fides/pull/4557)
- Custom privacy request field support for consent requests [#4546](https://github.com/ethyca/fides/pull/4546)
- Support GPP in privacy notices [#4554](https://github.com/ethyca/fides/pull/4554)

### Changed

- Redesigned nav bar for the admin UI [#4548](https://github.com/ethyca/fides/pull/4548)
- Fides.js GPP for US geographies now derives values from backend privacy notices [#4559](https://github.com/ethyca/fides/pull/4559)
- No longer generate the `vendors_disclosed` section of the TC string in `fides.js` [#4553](https://github.com/ethyca/fides/pull/4553)
- Changed consent management vendor add flow [#4550](https://github.com/ethyca/fides/pull/4550)

### Fixed

- Fixed an issue blocking Salesforce sandbox accounts from refreshing tokens [#4547](https://github.com/ethyca/fides/pull/4547)
- Fixed DSR zip packages to be unzippable on Windows [#4549](https://github.com/ethyca/fides/pull/4549)
- Fixed browser compatibility issues with Object.hasOwn [#4568](https://github.com/ethyca/fides/pull/4568)

### Developer Experience

- Switch to anyascii for unicode transliteration [#4550](https://github.com/ethyca/fides/pull/4564)

## [2.27.0](https://github.com/ethyca/fides/compare/2.26.0...2.27.0)

### Added

- Tooltip and styling for disabled rows in add multiple vendor view [#4498](https://github.com/ethyca/fides/pull/4498)
- Preliminary GPP support for US regions [#4498](https://github.com/ethyca/fides/pull/4504)
- Access and erasure support for Statsig Enterprise [#4429](https://github.com/ethyca/fides/pull/4429)
- New page for setting locations [#4517](https://github.com/ethyca/fides/pull/4517)
- New modal for setting granular locations [#4531](https://github.com/ethyca/fides/pull/4531)
- New page for setting regulations [#4530](https://github.com/ethyca/fides/pull/4530)
- Update fides.js to support multiple descriptions (banner, overlay) and render HTML descriptions [#4542](https://github.com/ethyca/fides/pull/4542)

### Fixed

- Fixed incorrect Compass button behavior in system form [#4508](https://github.com/ethyca/fides/pull/4508)
- Omit certain fields from system payload when empty [#4508](https://github.com/ethyca/fides/pull/4525)
- Fixed issues with Compass vendor selector behavior [#4521](https://github.com/ethyca/fides/pull/4521)
- Fixed an issue where the background overlay remained visible after saving consent preferences [#4515](https://github.com/ethyca/fides/pull/4515)
- Fixed system name being editable when editing GVL systems [#4533](https://github.com/ethyca/fides/pull/4533)
- Fixed an issue where a privacy policy link could not be removed from privacy experiences [#4542](https://github.com/ethyca/fides/pull/4542)

### Changed

- Upgrade to use Fideslang `3.0.0` and remove associated concepts [#4502](https://github.com/ethyca/fides/pull/4502)
- Model overhaul for saving privacy preferences and notices served [#4481](https://github.com/ethyca/fides/pull/4481)
- Moves served notice endpoints, consent reporting, purpose endpoints and TCF queries to plus [#4481](https://github.com/ethyca/fides/pull/4481)
- Moves served notice endpoints, consent reporting, and TCF queries to plus [#4481](https://github.com/ethyca/fides/pull/4481)
- Update frontend to account for changes to notices served and preferences saved APIs [#4518](https://github.com/ethyca/fides/pull/4518)
- `fides.js` now sets `supportsOOB` to `false` [#4516](https://github.com/ethyca/fides/pull/4516)
- Save consent method ("accept", "reject", "save", etc.) to `fides_consent` cookie as extra metadata [#4529](https://github.com/ethyca/fides/pull/4529)
- Allow CORS for privacy center `fides.js` and `fides-ext-gpp.js` endpoints
- Replace `GPP_EXT_PATH` env var in favor of a more flexible `FIDES_JS_BASE_URL` environment variable
- Change vendor add modal on consent configuration screen to use new vendor selector [#4532](https://github.com/ethyca/fides/pull/4532)
- Remove vendor add modal [#4535](https://github.com/ethyca/fides/pull/4535)

## [2.26.0](https://github.com/ethyca/fides/compare/2.25.0...main)

### Added

- Dynamic importing for GPP bundle [#4447](https://github.com/ethyca/fides/pull/4447)
- Paging to vendors in the TCF overlay [#4463](https://github.com/ethyca/fides/pull/4463)
- New purposes endpoint and indices to improve system lookups [#4452](https://github.com/ethyca/fides/pull/4452)
- Cypress tests for fides.js GPP extension [#4476](https://github.com/ethyca/fides/pull/4476)
- Add support for global TCF Purpose Overrides [#4464](https://github.com/ethyca/fides/pull/4464)
- TCF override management [#4484](https://github.com/ethyca/fides/pull/4484)
- Readonly consent management table and modal [#4456](https://github.com/ethyca/fides/pull/4456), [#4477](https://github.com/ethyca/fides/pull/4477)
- Access and erasure support for Gong [#4461](https://github.com/ethyca/fides/pull/4461)
- Add new UI for CSV consent reporting [#4488](https://github.com/ethyca/fides/pull/4488)
- Option to prevent the dismissal of the consent banner and modal [#4470](https://github.com/ethyca/fides/pull/4470)

### Changed

- Increased max number of preferences allowed in privacy preference API calls [#4469](https://github.com/ethyca/fides/pull/4469)
- Reduce size of tcf_consent payload in fides_consent cookie [#4480](https://github.com/ethyca/fides/pull/4480)
- Change log level for FidesUserPermission retrieval to `debug` [#4482](https://github.com/ethyca/fides/pull/4482)
- Remove Add Vendor button from the Manage your vendors page[#4509](https://github.com/ethyca/fides/pull/4509)

### Fixed

- Fix type errors when TCF vendors have no dataDeclaration [#4465](https://github.com/ethyca/fides/pull/4465)
- Fixed an error where editing an AC system would mistakenly lock it for GVL [#4471](https://github.com/ethyca/fides/pull/4471)
- Refactor custom Get Preferences function to occur after our CMP API initialization [#4466](https://github.com/ethyca/fides/pull/4466)
- Fix an error where a connector response value of None causes a DSR failure due to a missing value [#4483](https://github.com/ethyca/fides/pull/4483)
- Fixed system name being non-editable when locked for GVL [#4475](https://github.com/ethyca/fides/pull/4475)
- Fixed a bug with "null" values for retention period field on data uses [#4487](https://github.com/ethyca/fides/pull/4487)

## [2.25.0](https://github.com/ethyca/fides/compare/2.24.1...2.25.0)

### Added

- Stub for initial GPP support [#4431](https://github.com/ethyca/fides/pull/4431)
- Added confirmation modal on deleting a data use declaration [#4439](https://github.com/ethyca/fides/pull/4439)
- Added feature flag for separating system name and Compass vendor selector [#4437](https://github.com/ethyca/fides/pull/4437)
- Fire GPP events per spec [#4433](https://github.com/ethyca/fides/pull/4433)
- New override option `fides_tcf_gdpr_applies` for setting `gdprApplies` on the CMP API [#4453](https://github.com/ethyca/fides/pull/4453)

### Changed

- Improved bulk vendor adding table UX [#4425](https://github.com/ethyca/fides/pull/4425)
- Flexible legal basis for processing has a db default of True [#4434](https://github.com/ethyca/fides/pull/4434)
- Give contributor role access to config API, including cors origin updates [#4438](https://github.com/ethyca/fides/pull/4438)
- Disallow setting `*` and other non URL values for `security.cors_origins` config property via the API [#4438](https://github.com/ethyca/fides/pull/4438)
- Consent modal hides the opt-in/opt-out buttons if only one privacy notice is enabled [#4441](https://github.com/ethyca/fides/pull/4441)
- Initialize TCF stub earlier [#4453](https://github.com/ethyca/fides/pull/4453)
- Change focus outline color of form inputs [#4467](https://github.com/ethyca/fides/pull/4467)

### Fixed

- Fixed a bug where selected vendors in "configure consent" add vendor modal were unstyled [#4454](https://github.com/ethyca/fides/pull/4454)
- Use correct defaults when there is no associated preference in the cookie [#4451](https://github.com/ethyca/fides/pull/4451)
- IP Addresses behind load balancers for consent reporting [#4440](https://github.com/ethyca/fides/pull/4440)

## [2.24.1](https://github.com/ethyca/fides/compare/2.24.0...2.24.1)

### Added

- Logging when root user and client credentials are used [#4432](https://github.com/ethyca/fides/pull/4432)
- Allow for custom path at which to retrieve Fides override options [#4462](https://github.com/ethyca/fides/pull/4462)

### Changed

- Run fides with non-root user [#4421](https://github.com/ethyca/fides/pull/4421)

## [2.24.0](https://github.com/ethyca/fides/compare/2.23.3...2.24.0)

### Added

- Adds fides_disable_banner config option to Fides.js [#4378](https://github.com/ethyca/fides/pull/4378)
- Deletions that fail due to foreign key constraints will now be more clearly communicated [#4406](https://github.com/ethyca/fides/pull/4378)
- Added support for a custom get preferences API call provided through Fides.init [#4375](https://github.com/ethyca/fides/pull/4375)
- Hidden custom privacy request fields in the Privacy Center [#4370](https://github.com/ethyca/fides/pull/4370)
- Backend System-level Cookie Support [#4383](https://github.com/ethyca/fides/pull/4383)
- High Level Tracking of Compass System Sync [#4397](https://github.com/ethyca/fides/pull/4397)
- Erasure support for Qualtrics [#4371](https://github.com/ethyca/fides/pull/4371)
- Erasure support for Ada Chatbot [#4382](https://github.com/ethyca/fides/pull/4382)
- Erasure support for Typeform [#4366](https://github.com/ethyca/fides/pull/4366)
- Added notice that a system is GVL when adding/editing from system form [#4327](https://github.com/ethyca/fides/pull/4327)
- Added the ability to select the request types to enable per integration (for plus users) [#4374](https://github.com/ethyca/fides/pull/4374)
- Adds support for custom get experiences fn and custom patch notices served fn [#4410](https://github.com/ethyca/fides/pull/4410)
- Adds more granularity to tracking consent method, updates custom savePreferencesFn and FidesUpdated event to take consent method [#4419](https://github.com/ethyca/fides/pull/4419)

### Changed

- Add filtering and pagination to bulk vendor add table [#4351](https://github.com/ethyca/fides/pull/4351)
- Determine if the TCF overlay needs to surface based on backend calculated version hash [#4356](https://github.com/ethyca/fides/pull/4356)
- Moved Experiences and Preferences endpoints to Plus to take advantage of dynamic GVL [#4367](https://github.com/ethyca/fides/pull/4367)
- Add legal bases to Special Purpose schemas on the backend for display [#4387](https://github.com/ethyca/fides/pull/4387)
- "is_service_specific" default updated when building TC strings on the backend [#4377](https://github.com/ethyca/fides/pull/4377)
- "isServiceSpecific" default updated when building TC strings on the frontend [#4384](https://github.com/ethyca/fides/pull/4384)
- Redact cli, database, and redis configuration information from GET api/v1/config API request responses. [#4379](https://github.com/ethyca/fides/pull/4379)
- Button ordering in fides.js UI [#4407](https://github.com/ethyca/fides/pull/4407)
- Add different classnames to consent buttons for easier selection [#4411](https://github.com/ethyca/fides/pull/4411)
- Updates default consent preference to opt-out for TCF when fides_string exists [#4430](https://github.com/ethyca/fides/pull/4430)

### Fixed

- Persist bulk system add filter modal state [#4412](https://github.com/ethyca/fides/pull/4412)
- Fixing labels for request type field [#4414](https://github.com/ethyca/fides/pull/4414)
- User preferences from cookie should always override experience preferences [#4405](https://github.com/ethyca/fides/pull/4405)
- Allow fides_consent cookie to be set from a subdirectory [#4426](https://github.com/ethyca/fides/pull/4426)

### Security

-- Use a more cryptographically secure random function for security code generation

## [2.23.3](https://github.com/ethyca/fides/compare/2.23.2...2.23.3)

### Fixed

- Fix button arrangment and spacing for TCF and non-TCF consent overlay banner and modal [#4391](https://github.com/ethyca/fides/pull/4391)
- Replaced h1 element with div to use exisitng fides styles in consent modal [#4399](https://github.com/ethyca/fides/pull/4399)
- Fixed privacy policy alignment for non-TCF consent overlay banner and modal [#4403](https://github.com/ethyca/fides/pull/4403)
- Fix dynamic class name for TCF-variant of consent banner [#4404](https://github.com/ethyca/fides/pull/4403)

### Security

-- Fix an HTML Injection vulnerability in DSR Packages

## [2.23.2](https://github.com/ethyca/fides/compare/2.23.1...2.23.2)

### Fixed

- Fixed fides.css to vary banner width based on tcf [[#4381](https://github.com/ethyca/fides/issues/4381)]

## [2.23.1](https://github.com/ethyca/fides/compare/2.23.0...2.23.1)

### Changed

- Refactor Fides.js embedded modal to not use A11y dialog [#4355](https://github.com/ethyca/fides/pull/4355)
- Only call `FidesUpdated` when a preference has been saved, not during initialization [#4365](https://github.com/ethyca/fides/pull/4365)
- Updated double toggle styling in favor of single toggles with a radio group to select legal basis [#4376](https://github.com/ethyca/fides/pull/4376)

### Fixed

- Handle invalid `fides_string` when passed in as an override [#4350](https://github.com/ethyca/fides/pull/4350)
- Bug where vendor opt-ins would not initialize properly based on a `fides_string` in the TCF overlay [#4368](https://github.com/ethyca/fides/pull/4368)

## [2.23.0](https://github.com/ethyca/fides/compare/2.22.1...2.23.0)

### Added

- Added support for 3 additional config variables in Fides.js: fidesEmbed, fidesDisableSaveApi, and fidesTcString [#4262](https://github.com/ethyca/fides/pull/4262)
- Added support for fidesEmbed, fidesDisableSaveApi, and fidesTcString to be passed into Fides.js via query param, cookie, or window object [#4297](https://github.com/ethyca/fides/pull/4297)
- New privacy center environment variables `FIDES_PRIVACY_CENTER__IS_FORCED_TCF` which can make the privacy center always return the TCF bundle (`fides-tcf.js`) [#4312](https://github.com/ethyca/fides/pull/4312)
- Added a `FidesUIChanged` event to Fides.js to track when user preferences change without being saved [#4314](https://github.com/ethyca/fides/pull/4314) and [#4253](https://github.com/ethyca/fides/pull/4253)
- Add AC Systems to the TCF Overlay under Vendor Consents section [#4266](https://github.com/ethyca/fides/pull/4266/)
- Added bulk system/vendor creation component [#4309](https://github.com/ethyca/fides/pull/4309/)
- Support for passing in an AC string as part of a fides string for the TCF overlay [#4308](https://github.com/ethyca/fides/pull/4308)
- Added support for overriding the save user preferences API call with a custom fn provided through Fides.init [#4318](https://github.com/ethyca/fides/pull/4318)
- Return AC strings in GET Privacy Experience meta and allow saving preferences against AC strings [#4295](https://github.com/ethyca/fides/pull/4295)
- New GET Privacy Experience Meta Endpoint [#4328](https://github.com/ethyca/fides/pull/4328)
- Access and erasure support for SparkPost [#4328](https://github.com/ethyca/fides/pull/4238)
- Access and erasure support for Iterate [#4332](https://github.com/ethyca/fides/pull/4332)
- SSH Support for MySQL connections [#4310](https://github.com/ethyca/fides/pull/4310)
- Added served notice history IDs to the TCF privacy preference API calls [#4161](https://github.com/ethyca/fides/pull/4161)

### Fixed

- Cleans up CSS for fidesEmbed mode [#4306](https://github.com/ethyca/fides/pull/4306)
- Stacks that do not have any purposes will no longer render an empty purpose block [#4278](https://github.com/ethyca/fides/pull/4278)
- Forcing hidden sections to use display none [#4299](https://github.com/ethyca/fides/pull/4299)
- Handles Hubspot requiring and email to be formatted as email when processing an erasure [#4322](https://github.com/ethyca/fides/pull/4322)
- Minor CSS improvements for the consent/TCF banners and modals [#4334](https://github.com/ethyca/fides/pull/4334)
- Consistent font sizes for labels in the system form and data use forms in the Admin UI [#4346](https://github.com/ethyca/fides/pull/4346)
- Bug where not all system forms would appear to save when used with Compass [#4347](https://github.com/ethyca/fides/pull/4347)
- Restrict TCF Privacy Experience Config if TCF is disabled [#4348](https://github.com/ethyca/fides/pull/4348)
- Removes overflow styling for embedded modal in Fides.js [#4345](https://github.com/ethyca/fides/pull/4345)

### Changed

- Derive cookie storage info, privacy policy and legitimate interest disclosure URLs, and data retention data from the data map instead of directly from gvl.json [#4286](https://github.com/ethyca/fides/pull/4286)
- Updated TCF Version for backend consent reporting [#4305](https://github.com/ethyca/fides/pull/4305)
- Update Version Hash Contents [#4313](https://github.com/ethyca/fides/pull/4313)
- Change vendor selector on system information form to typeahead[#4333](https://github.com/ethyca/fides/pull/4333)
- Updates experience API calls from Fides.js to include new meta field [#4335](https://github.com/ethyca/fides/pull/4335)

## [2.22.1](https://github.com/ethyca/fides/compare/2.22.0...2.22.1)

### Added

- Custom fields are now included in system history change tracking [#4294](https://github.com/ethyca/fides/pull/4294)

### Security

- Added hostname checks for external SaaS connector URLs [CVE-2023-46124](https://github.com/ethyca/fides/security/advisories/GHSA-jq3w-9mgf-43m4)
- Use a Pydantic URL type for privacy policy URLs [CVE-2023-46126](https://github.com/ethyca/fides/security/advisories/GHSA-fgjj-5jmr-gh83)
- Remove the CONFIG_READ scope from the Viewer role [CVE-2023-46125](https://github.com/ethyca/fides/security/advisories/GHSA-rjxg-rpg3-9r89)

## [2.22.0](https://github.com/ethyca/fides/compare/2.21.0...2.22.0)

### Added

- Added an option to link to vendor tab from an experience config description [#4191](https://github.com/ethyca/fides/pull/4191)
- Added two toggles for vendors in the TCF overlay, one for Consent, and one for Legitimate Interest [#4189](https://github.com/ethyca/fides/pull/4189)
- Added two toggles for purposes in the TCF overlay, one for Consent, and one for Legitimate Interest [#4234](https://github.com/ethyca/fides/pull/4234)
- Added support for new TCF-related fields on `System` and `PrivacyDeclaration` models [#4228](https://github.com/ethyca/fides/pull/4228)
- Support for AC string to `fides-tcf` [#4244](https://github.com/ethyca/fides/pull/4244)
- Support for `gvl` prefixed vendor IDs [#4247](https://github.com/ethyca/fides/pull/4247)

### Changed

- Removed `TCF_ENABLED` environment variable from the privacy center in favor of dynamically figuring out which `fides-js` bundle to send [#4131](https://github.com/ethyca/fides/pull/4131)
- Updated copy of info boxes on each TCF tab [#4191](https://github.com/ethyca/fides/pull/4191)
- Clarified messages for error messages presented during connector upload [#4198](https://github.com/ethyca/fides/pull/4198)
- Refactor legal basis dimension regarding how TCF preferences are saved and how the experience is built [#4201](https://github.com/ethyca/fides/pull/4201/)
- Add saving privacy preferences via a TC string [#4221](https://github.com/ethyca/fides/pull/4221)
- Updated fides server to use an environment variable for turning TCF on and off [#4220](https://github.com/ethyca/fides/pull/4220)
- Update frontend to use new legal basis dimension on vendors [#4216](https://github.com/ethyca/fides/pull/4216)
- Updated privacy center patch preferences call to handle updated API response [#4235](https://github.com/ethyca/fides/pull/4235)
- Added our CMP ID [#4233](https://github.com/ethyca/fides/pull/4233)
- Allow Admin UI users to turn on Configure Consent flag [#4246](https://github.com/ethyca/fides/pull/4246)
- Styling improvements for the fides.js consent banners and modals [#4222](https://github.com/ethyca/fides/pull/4222)
- Update frontend to handle updated Compass schema [#4254](https://github.com/ethyca/fides/pull/4254)
- Assume Universal Vendor ID usage in TC String translation [#4256](https://github.com/ethyca/fides/pull/4256)
- Changed vendor form on configuring consent page to use two-part selection for consent uses [#4251](https://github.com/ethyca/fides/pull/4251)
- Updated system form to have new TCF fields [#4271](https://github.com/ethyca/fides/pull/4271)
- Vendors disclosed string is now narrowed to only the vendors shown in the UI, not the whole GVL [#4250](https://github.com/ethyca/fides/pull/4250)
- Changed naming convention "fides_string" instead of "tc_string" for developer friendly consent API's [#4267](https://github.com/ethyca/fides/pull/4267)

### Fixed

- TCF overlay can initialize its consent preferences from a cookie [#4124](https://github.com/ethyca/fides/pull/4124)
- Various improvements to the TCF modal such as vendor storage disclosures, vendor counts, privacy policies, etc. [#4167](https://github.com/ethyca/fides/pull/4167)
- An issue where Braze could not mask an email due to formatting [#4187](https://github.com/ethyca/fides/pull/4187)
- An issue where email was not being overridden correctly for Braze and Domo [#4196](https://github.com/ethyca/fides/pull/4196)
- Use `stdRetention` when there is not a specific value for a purpose's data retention [#4199](https://github.com/ethyca/fides/pull/4199)
- Updating the unflatten_dict util to accept flattened dict values [#4200](https://github.com/ethyca/fides/pull/4200)
- Minor CSS styling fixes for the consent modal [#4252](https://github.com/ethyca/fides/pull/4252)
- Additional styling fixes for issues caused by a CSS reset [#4268](https://github.com/ethyca/fides/pull/4268)
- Bug where vendor legitimate interests would not be set unless vendor consents were first set [#4250](https://github.com/ethyca/fides/pull/4250)
- Vendor count over-counting in TCF overlay [#4275](https://github.com/ethyca/fides/pull/4275)

## [2.21.0](https://github.com/ethyca/fides/compare/2.20.2...2.21.0)

### Added

- "Add a vendor" flow to configuring consent page [#4107](https://github.com/ethyca/fides/pull/4107)
- Initial TCF Backend Support [#3804](https://github.com/ethyca/fides/pull/3804)
- Add initial layer to TCF modal [#3956](https://github.com/ethyca/fides/pull/3956)
- Support for rendering in the TCF modal whether or not a vendor is part of the GVL [#3972](https://github.com/ethyca/fides/pull/3972)
- Features and legal bases dropdown for TCF modal [#3995](https://github.com/ethyca/fides/pull/3995)
- TCF CMP stub API [#4000](https://github.com/ethyca/fides/pull/4000)
- Fides-js can now display preliminary TCF data [#3879](https://github.com/ethyca/fides/pull/3879)
- Fides-js can persist TCF preferences to the backend [#3887](https://github.com/ethyca/fides/pull/3887)
- TCF modal now supports setting legitimate interest fields [#4037](https://github.com/ethyca/fides/pull/4037)
- Embed the GVL in the GET Experiences response [#4143](https://github.com/ethyca/fides/pull/4143)
- Button to view how many vendors and to open the vendor tab in the TCF modal [#4144](https://github.com/ethyca/fides/pull/4144)
- "Edit vendor" flow to configuring consent page [#4162](https://github.com/ethyca/fides/pull/4162)
- TCF overlay description updates [#4051] https://github.com/ethyca/fides/pull/4151
- Added developer-friendly TCF information under Experience meta [#4160](https://github.com/ethyca/fides/pull/4160/)
- Added fides.css customization for Plus users [#4136](https://github.com/ethyca/fides/pull/4136)

### Changed

- Added further config options to customize the privacy center [#4090](https://github.com/ethyca/fides/pull/4090)
- CORS configuration page [#4073](https://github.com/ethyca/fides/pull/4073)
- Refactored `fides.js` components so that they can take data structures that are not necessarily privacy notices [#3870](https://github.com/ethyca/fides/pull/3870)
- Use hosted GVL.json from the backend [#4159](https://github.com/ethyca/fides/pull/4159)
- Features and Special Purposes in the TCF modal do not render toggles [#4139](https://github.com/ethyca/fides/pull/4139)
- Moved the initial TCF layer to the banner [#4142](https://github.com/ethyca/fides/pull/4142)
- Misc copy changes for the system history table and modal [#4146](https://github.com/ethyca/fides/pull/4146)

### Fixed

- Allows CDN to cache empty experience responses from fides.js API [#4113](https://github.com/ethyca/fides/pull/4113)
- Fixed `identity_special_purpose` unique constraint definition [#4174](https://github.com/ethyca/fides/pull/4174/files)

## [2.20.2](https://github.com/ethyca/fides/compare/2.20.1...2.20.2)

### Fixed

- added version_added, version_deprecated, and replaced_by to data use, data subject, and data category APIs [#4135](https://github.com/ethyca/fides/pull/4135)
- Update fides.js to not fetch experience client-side if pre-fetched experience is empty [#4149](https://github.com/ethyca/fides/pull/4149)
- Erasure privacy requests now pause for input if there are any manual process integrations [#4115](https://github.com/ethyca/fides/pull/4115)
- Caching the values of authorization_required and user_guide on the connector templates to improve performance [#4128](https://github.com/ethyca/fides/pull/4128)

## [2.20.1](https://github.com/ethyca/fides/compare/2.20.0...2.20.1)

### Fixed

- Avoid un-optimized query pattern in bulk `GET /system` endpoint [#4120](https://github.com/ethyca/fides/pull/4120)

## [2.20.0](https://github.com/ethyca/fides/compare/2.19.1...2.20.0)

### Added

- Initial page for configuring consent [#4069](https://github.com/ethyca/fides/pull/4069)
- Vendor cookie table for configuring consent [#4082](https://github.com/ethyca/fides/pull/4082)

### Changed

- Refactor how multiplatform builds are handled [#4024](https://github.com/ethyca/fides/pull/4024)
- Added new Performance-related nox commands and included them as part of the CI suite [#3997](https://github.com/ethyca/fides/pull/3997)
- Added dictionary suggestions for data uses [4035](https://github.com/ethyca/fides/pull/4035)
- Privacy notice regions now render human readable names instead of country codes [#4029](https://github.com/ethyca/fides/pull/4029)
- Privacy notice templates are disabled by default [#4010](https://github.com/ethyca/fides/pull/4010)
- Added optional "skip_processing" flag to collections for DSR processing [#4047](https://github.com/ethyca/fides/pull/4047)
- Admin UI now shows all privacy notices with an indicator of whether they apply to any systems [#4010](https://github.com/ethyca/fides/pull/4010)
- Add case-insensitive privacy experience region filtering [#4058](https://github.com/ethyca/fides/pull/4058)
- Adds check for fetch before loading fetch polyfill for fides.js [#4074](https://github.com/ethyca/fides/pull/4074)
- Updated to support Fideslang 2.0, including data migrations [#3933](https://github.com/ethyca/fides/pull/3933)
- Disable notices that are not systems applicable to support new UI [#4094](https://github.com/ethyca/fides/issues/4094)

### Fixed

- Ensures that fides.js toggles are not hidden by other CSS libs [#4075](https://github.com/ethyca/fides/pull/4075)
- Migrate system > meta > vendor > id to system > meta [#4088](https://github.com/ethyca/fides/pull/4088)
- Enable toggles in various tables now render an error toast if an error occurs [#4095](https://github.com/ethyca/fides/pull/4095)
- Fixed a bug where an unsaved changes notification modal would appear even without unsaved changes [#4095](https://github.com/ethyca/fides/pull/4070)

## [2.19.1](https://github.com/ethyca/fides/compare/2.19.0...2.19.1)

### Fixed

- re-enable custom fields for new data use form [#4050](https://github.com/ethyca/fides/pull/4050)
- fix issue with saving source and destination systems [#4065](https://github.com/ethyca/fides/pull/4065)

### Added

- System history UI with diff modal [#4021](https://github.com/ethyca/fides/pull/4021)
- Relax system legal basis for transfers to be any string [#4049](https://github.com/ethyca/fides/pull/4049)

## [2.19.0](https://github.com/ethyca/fides/compare/2.18.0...2.19.0)

### Added

- Add dictionary suggestions [#3937](https://github.com/ethyca/fides/pull/3937), [#3988](https://github.com/ethyca/fides/pull/3988)
- Added new endpoints for healthchecks [#3947](https://github.com/ethyca/fides/pull/3947)
- Added vendor list dropdown [#3857](https://github.com/ethyca/fides/pull/3857)
- Access support for Adobe Sign [#3504](https://github.com/ethyca/fides/pull/3504)

### Fixed

- Fixed issue when generating masked values for invalid data paths [#3906](https://github.com/ethyca/fides/pull/3906)
- Code reload now works when running `nox -s dev` [#3914](https://github.com/ethyca/fides/pull/3914)
- Reduce verbosity of privacy center logging further [#3915](https://github.com/ethyca/fides/pull/3915)
- Resolved an issue where the integration dropdown input lost focus during typing. [#3917](https://github.com/ethyca/fides/pull/3917)
- Fixed dataset issue that was preventing the Vend connector from loading during server startup [#3923](https://github.com/ethyca/fides/pull/3923)
- Adding version check to version-dependent migration script [#3951](https://github.com/ethyca/fides/pull/3951)
- Fixed a bug where some fields were not saving correctly on the system form [#3975](https://github.com/ethyca/fides/pull/3975)
- Changed "retention period" field in privacy declaration form from number input to text input [#3980](https://github.com/ethyca/fides/pull/3980)
- Fixed issue where unsaved changes modal appears incorrectly [#4005](https://github.com/ethyca/fides/pull/4005)
- Fixed banner resurfacing after user consent for pre-fetch experience [#4009](https://github.com/ethyca/fides/pull/4009)

### Changed

- Systems and Privacy Declaration schema and data migration to support the Dictionary [#3901](https://github.com/ethyca/fides/pull/3901)
- The integration search dropdown is now case-insensitive [#3916](https://github.com/ethyca/fides/pull/3916)
- Removed deprecated fields from the taxonomy editor [#3909](https://github.com/ethyca/fides/pull/3909)
- Bump PyMSSQL version and remove workarounds [#3996](https://github.com/ethyca/fides/pull/3996)
- Removed reset suggestions button [#4007](https://github.com/ethyca/fides/pull/4007)
- Admin ui supports fides cloud config API [#4034](https://github.com/ethyca/fides/pull/4034)

### Security

- Resolve custom integration upload RCE vulnerability [CVE-2023-41319](https://github.com/ethyca/fides/security/advisories/GHSA-p6p2-qq95-vq5h)

## [2.18.0](https://github.com/ethyca/fides/compare/2.17.0...2.18.0)

### Added

- Additional consent reporting calls from `fides-js` [#3845](https://github.com/ethyca/fides/pull/3845)
- Additional consent reporting calls from privacy center [#3847](https://github.com/ethyca/fides/pull/3847)
- Access support for Recurly [#3595](https://github.com/ethyca/fides/pull/3595)
- HTTP Logging for the Privacy Center [#3783](https://github.com/ethyca/fides/pull/3783)
- UI support for OAuth2 authorization flow [#3819](https://github.com/ethyca/fides/pull/3819)
- Changes in the `data` directory now trigger a server reload (for local development) [#3874](https://github.com/ethyca/fides/pull/3874)

### Fixed

- Fix datamap zoom for low system counts [#3835](https://github.com/ethyca/fides/pull/3835)
- Fixed connector forms with external dataset reference fields [#3873](https://github.com/ethyca/fides/pull/3873)
- Fix ability to make server side API calls from privacy-center [#3895](https://github.com/ethyca/fides/pull/3895)

### Changed

- Simplified the file structure for HTML DSR packages [#3848](https://github.com/ethyca/fides/pull/3848)
- Simplified the database health check to improve `/health` performance [#3884](https://github.com/ethyca/fides/pull/3884)
- Changed max width of form components in "system information" form tab [#3864](https://github.com/ethyca/fides/pull/3864)
- Remove manual system selection screen [#3865](https://github.com/ethyca/fides/pull/3865)
- System and integration identifiers are now auto-generated [#3868](https://github.com/ethyca/fides/pull/3868)

## [2.17.0](https://github.com/ethyca/fides/compare/2.16.0...2.17.0)

### Added

- Tab component for `fides-js` [#3782](https://github.com/ethyca/fides/pull/3782)
- Added toast for successfully linking an existing integration to a system [#3826](https://github.com/ethyca/fides/pull/3826)
- Various other UI components for `fides-js` to support upcoming TCF modal [#3803](https://github.com/ethyca/fides/pull/3803)
- Allow items in taxonomy to be enabled or disabled [#3844](https://github.com/ethyca/fides/pull/3844)

### Developer Experience

- Changed where db-dependent routers were imported to avoid dependency issues [#3741](https://github.com/ethyca/fides/pull/3741)

### Changed

- Bumped supported Python versions to `3.10.12`, `3.9.17`, and `3.8.17` [#3733](https://github.com/ethyca/fides/pull/3733)
- Logging Updates [#3758](https://github.com/ethyca/fides/pull/3758)
- Add polyfill service to fides-js route [#3759](https://github.com/ethyca/fides/pull/3759)
- Show/hide integration values [#3775](https://github.com/ethyca/fides/pull/3775)
- Sort system cards alphabetically by name on "View systems" page [#3781](https://github.com/ethyca/fides/pull/3781)
- Update admin ui to use new integration delete route [#3785](https://github.com/ethyca/fides/pull/3785)
- Pinned `pymssql` and `cython` dependencies to avoid build issues on ARM machines [#3829](https://github.com/ethyca/fides/pull/3829)

### Removed

- Removed "Custom field(s) successfully saved" toast [#3779](https://github.com/ethyca/fides/pull/3779)

### Added

- Record when consent is served [#3777](https://github.com/ethyca/fides/pull/3777)
- Add an `active` property to taxonomy elements [#3784](https://github.com/ethyca/fides/pull/3784)
- Erasure support for Heap [#3599](https://github.com/ethyca/fides/pull/3599)

### Fixed

- Privacy notice UI's list of possible regions now matches the backend's list [#3787](https://github.com/ethyca/fides/pull/3787)
- Admin UI "property does not existing" build issue [#3831](https://github.com/ethyca/fides/pull/3831)
- Flagging sensitive inputs as passwords to mask values during entry [#3843](https://github.com/ethyca/fides/pull/3843)

## [2.16.0](https://github.com/ethyca/fides/compare/2.15.1...2.16.0)

### Added

- Empty state for when there are no relevant privacy notices in the privacy center [#3640](https://github.com/ethyca/fides/pull/3640)
- GPC indicators in fides-js banner and modal [#3673](https://github.com/ethyca/fides/pull/3673)
- Include `data_use` and `data_category` metadata in `upload` of access results [#3674](https://github.com/ethyca/fides/pull/3674)
- Add enable/disable toggle to integration tab [#3593] (https://github.com/ethyca/fides/pull/3593)

### Fixed

- Render linebreaks in the Fides.js overlay descriptions, etc. [#3665](https://github.com/ethyca/fides/pull/3665)
- Broken link to Fides docs site on the About Fides page in Admin UI [#3643](https://github.com/ethyca/fides/pull/3643)
- Add Systems Applicable Filter to Privacy Experience List [#3654](https://github.com/ethyca/fides/pull/3654)
- Privacy center and fides-js now pass in `Unescape-Safestr` as a header so that special characters can be rendered properly [#3706](https://github.com/ethyca/fides/pull/3706)
- Fixed ValidationError for saving PrivacyPreferences [#3719](https://github.com/ethyca/fides/pull/3719)
- Fixed issue preventing ConnectionConfigs with duplicate names from saving [#3770](https://github.com/ethyca/fides/pull/3770)
- Fixed creating and editing manual integrations [#3772](https://github.com/ethyca/fides/pull/3772)
- Fix lingering integration artifacts by cascading deletes from System [#3771](https://github.com/ethyca/fides/pull/3771)

### Developer Experience

- Reorganized some `api.api.v1` code to avoid circular dependencies on `quickstart` [#3692](https://github.com/ethyca/fides/pull/3692)
- Treat underscores as special characters in user passwords [#3717](https://github.com/ethyca/fides/pull/3717)
- Allow Privacy Notices banner and modal to scroll as needed [#3713](https://github.com/ethyca/fides/pull/3713)
- Make malicious url test more robust to environmental differences [#3748](https://github.com/ethyca/fides/pull/3748)
- Ignore type checker on click decorators to bypass known issue with `click` version `8.1.4` [#3746](https://github.com/ethyca/fides/pull/3746)

### Changed

- Moved GPC preferences slightly earlier in Fides.js lifecycle [#3561](https://github.com/ethyca/fides/pull/3561)
- Changed results from clicking "Test connection" to be a toast instead of statically displayed on the page [#3700](https://github.com/ethyca/fides/pull/3700)
- Moved "management" tab from nav into settings icon in top right [#3701](https://github.com/ethyca/fides/pull/3701)
- Remove name and description fields from integration form [#3684](https://github.com/ethyca/fides/pull/3684)
- Update EU PrivacyNoticeRegion codes and allow experience filtering to drop back to country filtering if region not found [#3630](https://github.com/ethyca/fides/pull/3630)
- Fields with default fields are now flagged as required in the front-end [#3694](https://github.com/ethyca/fides/pull/3694)
- In "view systems", system cards can now be clicked and link to that system's `configure/[id]` page [#3734](https://github.com/ethyca/fides/pull/3734)
- Enable privacy notice and privacy experience feature flags by default [#3773](https://github.com/ethyca/fides/pull/3773)

### Security

- Resolve Zip bomb file upload vulnerability [CVE-2023-37480](https://github.com/ethyca/fides/security/advisories/GHSA-g95c-2jgm-hqc6)
- Resolve SVG bomb (billion laughs) file upload vulnerability [CVE-2023-37481](https://github.com/ethyca/fides/security/advisories/GHSA-3rw2-wfc8-wmj5)

## [2.15.1](https://github.com/ethyca/fides/compare/2.15.0...2.15.1)

### Added

- Set `sslmode` to `prefer` if connecting to Redshift via ssh [#3685](https://github.com/ethyca/fides/pull/3685)

### Changed

- Privacy center action cards are now able to expand to accommodate longer text [#3669](https://github.com/ethyca/fides/pull/3669)
- Update integration endpoint permissions [#3707](https://github.com/ethyca/fides/pull/3707)

### Fixed

- Handle names with a double underscore when processing access and erasure requests [#3688](https://github.com/ethyca/fides/pull/3688)
- Allow Privacy Notices banner and modal to scroll as needed [#3713](https://github.com/ethyca/fides/pull/3713)

### Security

- Resolve path traversal vulnerability in webserver API [CVE-2023-36827](https://github.com/ethyca/fides/security/advisories/GHSA-r25m-cr6v-p9hq)

## [2.15.0](https://github.com/ethyca/fides/compare/2.14.1...2.15.0)

### Added

- Privacy center can now render its consent values based on Privacy Notices and Privacy Experiences [#3411](https://github.com/ethyca/fides/pull/3411)
- Add Google Tag Manager and Privacy Center ENV vars to sample app [#2949](https://github.com/ethyca/fides/pull/2949)
- Add `notice_key` field to Privacy Notice UI form [#3403](https://github.com/ethyca/fides/pull/3403)
- Add `identity` query param to the consent reporting API view [#3418](https://github.com/ethyca/fides/pull/3418)
- Use `rollup-plugin-postcss` to bundle and optimize the `fides.js` components CSS [#3411](https://github.com/ethyca/fides/pull/3411)
- Dispatch Fides.js lifecycle events on window (FidesInitialized, FidesUpdated) and cross-publish to Fides.gtm() integration [#3411](https://github.com/ethyca/fides/pull/3411)
- Added the ability to use custom CAs with Redis via TLS [#3451](https://github.com/ethyca/fides/pull/3451)
- Add default experience configs on startup [#3449](https://github.com/ethyca/fides/pull/3449)
- Load default privacy notices on startup [#3401](https://github.com/ethyca/fides/pull/3401)
- Add ability for users to pass in additional parameters for application database connection [#3450](https://github.com/ethyca/fides/pull/3450)
- Load default privacy notices on startup [#3401](https://github.com/ethyca/fides/pull/3401/files)
- Add ability for `fides-js` to make API calls to Fides [#3411](https://github.com/ethyca/fides/pull/3411)
- `fides-js` banner is now responsive across different viewport widths [#3411](https://github.com/ethyca/fides/pull/3411)
- Add ability to close `fides-js` banner and modal via a button or ESC [#3411](https://github.com/ethyca/fides/pull/3411)
- Add ability to open the `fides-js` modal from a link on the host site [#3411](https://github.com/ethyca/fides/pull/3411)
- GPC preferences are automatically applied via `fides-js` [#3411](https://github.com/ethyca/fides/pull/3411)
- Add new dataset route that has additional filters [#3558](https://github.com/ethyca/fides/pull/3558)
- Update dataset dropdown to use new api filter [#3565](https://github.com/ethyca/fides/pull/3565)
- Filter out saas datasets from the rest of the UI [#3568](https://github.com/ethyca/fides/pull/3568)
- Included optional env vars to have postgres or Redshift connected via bastion host [#3374](https://github.com/ethyca/fides/pull/3374/)
- Support for acknowledge button for notice-only Privacy Notices and to disable toggling them off [#3546](https://github.com/ethyca/fides/pull/3546)
- HTML format for privacy request storage destinations [#3427](https://github.com/ethyca/fides/pull/3427)
- Persistent message showing result and timestamp of last integration test to "Integrations" tab in system view [#3628](https://github.com/ethyca/fides/pull/3628)
- Access and erasure support for SurveyMonkey [#3590](https://github.com/ethyca/fides/pull/3590)
- New Cookies Table for storing cookies associated with systems and privacy declarations [#3572](https://github.com/ethyca/fides/pull/3572)
- `fides-js` and privacy center now delete cookies associated with notices that were opted out of [#3569](https://github.com/ethyca/fides/pull/3569)
- Cookie input field on system data use tab [#3571](https://github.com/ethyca/fides/pull/3571)

### Fixed

- Fix sample app `DATABASE_*` ENV vars for backwards compatibility [#3406](https://github.com/ethyca/fides/pull/3406)
- Fix overlay rendering issue by finding/creating a dedicated parent element for Preact [#3397](https://github.com/ethyca/fides/pull/3397)
- Fix the sample app privacy center link to be configurable [#3409](https://github.com/ethyca/fides/pull/3409)
- Fix CLI output showing a version warning for Snowflake [#3434](https://github.com/ethyca/fides/pull/3434)
- Flaky custom field Cypress test on systems page [#3408](https://github.com/ethyca/fides/pull/3408)
- Fix NextJS errors & warnings for Cookie House sample app [#3411](https://github.com/ethyca/fides/pull/3411)
- Fix bug where `fides-js` toggles were not reflecting changes from rejecting or accepting all notices [#3522](https://github.com/ethyca/fides/pull/3522)
- Remove the `fides-js` banner from tab order when it is hidden and move the overlay components to the top of the tab order. [#3510](https://github.com/ethyca/fides/pull/3510)
- Fix bug where `fides-js` toggle states did not always initialize properly [#3597](https://github.com/ethyca/fides/pull/3597)
- Fix race condition with consent modal link rendering [#3521](https://github.com/ethyca/fides/pull/3521)
- Hide custom fields section when there are no custom fields created [#3554](https://github.com/ethyca/fides/pull/3554)
- Disable connector dropdown in integration tab on save [#3552](https://github.com/ethyca/fides/pull/3552)
- Handles an edge case for non-existent identities with the Kustomer API [#3513](https://github.com/ethyca/fides/pull/3513)
- remove the configure privacy request tile from the home screen [#3555](https://github.com/ethyca/fides/pull/3555)
- Updated Privacy Experience Safe Strings Serialization [#3600](https://github.com/ethyca/fides/pull/3600/)
- Only create default experience configs on startup, not update [#3605](https://github.com/ethyca/fides/pull/3605)
- Update to latest asyncpg dependency to avoid build error [#3614](https://github.com/ethyca/fides/pull/3614)
- Fix bug where editing a data use on a system could delete existing data uses [#3627](https://github.com/ethyca/fides/pull/3627)
- Restrict Privacy Center debug logging to development-only [#3638](https://github.com/ethyca/fides/pull/3638)
- Fix bug where linking an integration would not update the tab when creating a new system [#3662](https://github.com/ethyca/fides/pull/3662)
- Fix dataset yaml not properly reflecting the dataset in the dropdown of system integrations tab [#3666](https://github.com/ethyca/fides/pull/3666)
- Fix privacy notices not being able to be edited via the UI after the addition of the `cookies` field [#3670](https://github.com/ethyca/fides/pull/3670)
- Add a transform in the case of `null` name fields in privacy declarations for the data use forms [#3683](https://github.com/ethyca/fides/pull/3683)

### Changed

- Enabled Privacy Experience beta flag [#3364](https://github.com/ethyca/fides/pull/3364)
- Reorganize CLI Command Source Files [#3491](https://github.com/ethyca/fides/pull/3491)
- Removed ExperienceConfig.delivery_mechanism constraint [#3387](https://github.com/ethyca/fides/pull/3387)
- Updated privacy experience UI forms to reflect updated experience config fields [#3402](https://github.com/ethyca/fides/pull/3402)
- Use a venv in the Dockerfile for installing Python deps [#3452](https://github.com/ethyca/fides/pull/3452)
- Bump SlowAPI Version [#3456](https://github.com/ethyca/fides/pull/3456)
- Bump Psycopg2-binary Version [#3473](https://github.com/ethyca/fides/pull/3473)
- Reduced duplication between PrivacyExperience and PrivacyExperienceConfig [#3470](https://github.com/ethyca/fides/pull/3470)
- Update privacy centre email and phone validation to allow for both to be blank [#3432](https://github.com/ethyca/fides/pull/3432)
- Moved connection configuration into the system portal [#3407](https://github.com/ethyca/fides/pull/3407)
- Update `fideslang` to `1.4.1` to allow arbitrary nested metadata on `System`s and `Dataset`s `meta` property [#3463](https://github.com/ethyca/fides/pull/3463)
- Remove form validation to allow both email & phone inputs for consent requests [#3529](https://github.com/ethyca/fides/pull/3529)
- Removed dataset dropdown from saas connector configuration [#3563](https://github.com/ethyca/fides/pull/3563)
- Removed `pyodbc` in favor of `pymssql` for handling SQL Server connections [#3435](https://github.com/ethyca/fides/pull/3435)
- Only create a PrivacyRequest when saving consent if at least one notice has system-wide enforcement [#3626](https://github.com/ethyca/fides/pull/3626)
- Increased the character limit for the `SafeStr` type from 500 to 32000 [#3647](https://github.com/ethyca/fides/pull/3647)
- Changed "connection" to "integration" on system view and edit pages [#3659](https://github.com/ethyca/fides/pull/3659)

### Developer Experience

- Add ability to pass ENV vars to both privacy center and sample app during `fides deploy` via `.env` [#2949](https://github.com/ethyca/fides/pull/2949)
- Handle an edge case when generating tags that finds them out of sequence [#3405](https://github.com/ethyca/fides/pull/3405)
- Add support for pushing `prerelease` and `rc` tagged images to Dockerhub [#3474](https://github.com/ethyca/fides/pull/3474)
- Optimize GitHub workflows used for docker image publishing [#3526](https://github.com/ethyca/fides/pull/3526)

### Removed

- Removed the deprecated `system_dependencies` from `System` resources, migrating to `egress` [#3285](https://github.com/ethyca/fides/pull/3285)

### Docs

- Updated developer docs for ARM platform users related to `pymssql` [#3615](https://github.com/ethyca/fides/pull/3615)

## [2.14.1](https://github.com/ethyca/fides/compare/2.14.0...2.14.1)

### Added

- Add `identity` query param to the consent reporting API view [#3418](https://github.com/ethyca/fides/pull/3418)
- Add privacy centre button text customisations [#3432](https://github.com/ethyca/fides/pull/3432)
- Add privacy centre favicon customisation [#3432](https://github.com/ethyca/fides/pull/3432)

### Changed

- Update privacy centre email and phone validation to allow for both to be blank [#3432](https://github.com/ethyca/fides/pull/3432)

## [2.14.0](https://github.com/ethyca/fides/compare/2.13.0...2.14.0)

### Added

- Add an automated test to check for `/fides-consent.js` backwards compatibility [#3289](https://github.com/ethyca/fides/pull/3289)
- Add infrastructure for "overlay" consent components (Preact, CSS bundling, etc.) and initial version of consent banner [#3191](https://github.com/ethyca/fides/pull/3191)
- Add the modal component of the "overlay" consent components [#3291](https://github.com/ethyca/fides/pull/3291)
- Added an `automigrate` database setting [#3220](https://github.com/ethyca/fides/pull/3220)
- Track Privacy Experience with Privacy Preferences [#3311](https://github.com/ethyca/fides/pull/3311)
- Add ability for `fides-js` to fetch its own geolocation [#3356](https://github.com/ethyca/fides/pull/3356)
- Add ability to select different locations in the "Cookie House" sample app [#3362](https://github.com/ethyca/fides/pull/3362)
- Added optional logging of resource changes on the server [#3331](https://github.com/ethyca/fides/pull/3331)

### Fixed

- Maintain casing differences within Snowflake datasets for proper DSR execution [#3245](https://github.com/ethyca/fides/pull/3245)
- Handle DynamoDB edge case where no attributes are defined [#3299](https://github.com/ethyca/fides/pull/3299)
- Support pseudonymous consent requests with `fides_user_device_id` for the new consent workflow [#3203](https://github.com/ethyca/fides/pull/3203)
- Fides user device id filter to GET Privacy Experience List endpoint to stash user preferences on embedded notices [#3302](https://github.com/ethyca/fides/pull/3302)
- Support for data categories on manual webhook fields [#3330](https://github.com/ethyca/fides/pull/3330)
- Added config-driven rendering to consent components [#3316](https://github.com/ethyca/fides/pull/3316)
- Pin `typing_extensions` dependency to `4.5.0` to work around a pydantic bug [#3357](https://github.com/ethyca/fides/pull/3357)

### Changed

- Explicitly escape/unescape certain fields instead of using SafeStr [#3144](https://github.com/ethyca/fides/pull/3144)
- Updated DynamoDB icon [#3296](https://github.com/ethyca/fides/pull/3296)
- Increased default page size for the connection type endpoint to 100 [#3298](https://github.com/ethyca/fides/pull/3298)
- Data model around PrivacyExperiences to better keep Privacy Notices and Experiences in sync [#3292](https://github.com/ethyca/fides/pull/3292)
- UI calls to support new PrivacyExperiences data model [#3313](https://github.com/ethyca/fides/pull/3313)
- Ensure email connectors respect the `notifications.notification_service_type` app config property if set [#3355](https://github.com/ethyca/fides/pull/3355)
- Rework Delighted connector so the `survey_response` endpoint depends on the `person` endpoint [3385](https://github.com/ethyca/fides/pull/3385)
- Remove logging within the Celery creation function [#3303](https://github.com/ethyca/fides/pull/3303)
- Update how generic endpoint generation works [#3304](https://github.com/ethyca/fides/pull/3304)
- Restrict strack-trace logging when not in Dev mode [#3081](https://github.com/ethyca/fides/pull/3081)
- Refactor CSS variables for `fides-js` to match brandable color palette [#3321](https://github.com/ethyca/fides/pull/3321)
- Moved all of the dirs from `fides.api.ops` into `fides.api` [#3318](https://github.com/ethyca/fides/pull/3318)
- Put global settings for fides.js on privacy center settings [#3333](https://github.com/ethyca/fides/pull/3333)
- Changed `fides db migrate` to `fides db upgrade` [#3342](https://github.com/ethyca/fides/pull/3342)
- Add required notice key to privacy notices [#3337](https://github.com/ethyca/fides/pull/3337)
- Make Privacy Experience List public, and separate public endpoint rate limiting [#3339](https://github.com/ethyca/fides/pull/3339)

### Developer Experience

- Add dispatch event when publishing a non-prod tag [#3317](https://github.com/ethyca/fides/pull/3317)
- Add OpenAPI (Swagger) documentation for Fides Privacy Center API endpoints (/fides.js) [#3341](https://github.com/ethyca/fides/pull/3341)

### Removed

- Remove `fides export` command and backing code [#3256](https://github.com/ethyca/fides/pull/3256)

## [2.13.0](https://github.com/ethyca/fides/compare/2.12.1...2.13.0)

### Added

- Connector for DynamoDB [#2998](https://github.com/ethyca/fides/pull/2998)
- Access and erasure support for Amplitude [#2569](https://github.com/ethyca/fides/pull/2569)
- Access and erasure support for Gorgias [#2444](https://github.com/ethyca/fides/pull/2444)
- Privacy Experience Bulk Create, Bulk Update, and Detail Endpoints [#3185](https://github.com/ethyca/fides/pull/3185)
- Initial privacy experience UI [#3186](https://github.com/ethyca/fides/pull/3186)
- A JavaScript modal to copy a script tag for `fides.js` [#3238](https://github.com/ethyca/fides/pull/3238)
- Access and erasure support for OneSignal [#3199](https://github.com/ethyca/fides/pull/3199)
- Add the ability to "inject" location into `/fides.js` bundles and cache responses for one hour [#3272](https://github.com/ethyca/fides/pull/3272)
- Prevent column sorts from resetting when data changes [#3290](https://github.com/ethyca/fides/pull/3290)

### Changed

- Merge instances of RTK `createApi` into one instance for better cache invalidation [#3059](https://github.com/ethyca/fides/pull/3059)
- Update custom field definition uniqueness to be case insensitive name per resource type [#3215](https://github.com/ethyca/fides/pull/3215)
- Restrict where privacy notices of certain consent mechanisms must be displayed [#3195](https://github.com/ethyca/fides/pull/3195)
- Merged the `lib` submodule into the `api.ops` submodule [#3134](https://github.com/ethyca/fides/pull/3134)
- Merged duplicate privacy declaration components [#3254](https://github.com/ethyca/fides/pull/3254)
- Refactor client applications into a monorepo with turborepo, extract fides-js into a standalone package, and improve privacy-center to load configuration at runtime [#3105](https://github.com/ethyca/fides/pull/3105)

### Fixed

- Prevent ability to unintentionally show "default" Privacy Center configuration, styles, etc. [#3242](https://github.com/ethyca/fides/pull/3242)
- Fix broken links to docs site pages in Admin UI [#3232](https://github.com/ethyca/fides/pull/3232)
- Repoint legacy docs site links to the new and improved docs site [#3167](https://github.com/ethyca/fides/pull/3167)
- Fix Cookie House Privacy Center styles for fides deploy [#3283](https://github.com/ethyca/fides/pull/3283)
- Maintain casing differences within Snowflake datasets for proper DSR execution [#3245](https://github.com/ethyca/fides/pull/3245)

### Developer Experience

- Use prettier to format _all_ source files in client packages [#3240](https://github.com/ethyca/fides/pull/3240)

### Deprecated

- Deprecate `fides export` CLI command as it is moving to `fidesplus` [#3264](https://github.com/ethyca/fides/pull/3264)

## [2.12.1](https://github.com/ethyca/fides/compare/2.12.0...2.12.1)

### Changed

- Updated how Docker version checks are handled and added an escape-hatch [#3218](https://github.com/ethyca/fides/pull/3218)

### Fixed

- Datamap export mitigation for deleted taxonomy elements referenced by declarations [#3214](https://github.com/ethyca/fides/pull/3214)
- Update datamap columns each time the page is visited [#3211](https://github.com/ethyca/fides/pull/3211)
- Ensure inactive custom fields are not returned for datamap response [#3223](https://github.com/ethyca/fides/pull/3223)

## [2.12.0](https://github.com/ethyca/fides/compare/2.11.0...2.12.0)

### Added

- Access and erasure support for Aircall [#2589](https://github.com/ethyca/fides/pull/2589)
- Access and erasure support for Klaviyo [#2501](https://github.com/ethyca/fides/pull/2501)
- Page to edit or add privacy notices [#3058](https://github.com/ethyca/fides/pull/3058)
- Side navigation bar can now also have children navigation links [#3099](https://github.com/ethyca/fides/pull/3099)
- Endpoints for consent reporting [#3095](https://github.com/ethyca/fides/pull/3095)
- Added manage custom fields page behind feature flag [#3089](https://github.com/ethyca/fides/pull/3089)
- Custom fields table [#3097](https://github.com/ethyca/fides/pull/3097)
- Custom fields form modal [#3165](https://github.com/ethyca/fides/pull/3165)
- Endpoints to save the new-style Privacy Preferences with respect to a fides user device id [#3132](https://github.com/ethyca/fides/pull/3132)
- Support `privacy_declaration` as a resource type for custom fields [#3149](https://github.com/ethyca/fides/pull/3149)
- Expose `id` field of embedded `privacy_declarations` on `system` API responses [#3157](https://github.com/ethyca/fides/pull/3157)
- Access and erasure support for Unbounce [#2697](https://github.com/ethyca/fides/pull/2697)
- Support pseudonymous consent requests with `fides_user_device_id` [#3158](https://github.com/ethyca/fides/pull/3158)
- Update `fides_consent` cookie format [#3158](https://github.com/ethyca/fides/pull/3158)
- Add custom fields to the data use declaration form [#3197](https://github.com/ethyca/fides/pull/3197)
- Added fides user device id as a ProvidedIdentityType [#3131](https://github.com/ethyca/fides/pull/3131)

### Changed

- The `cursor` pagination strategy now also searches for data outside of the `data_path` when determining the cursor value [#3068](https://github.com/ethyca/fides/pull/3068)
- Moved Privacy Declarations associated with Systems to their own DB table [#3098](https://github.com/ethyca/fides/pull/3098)
- More tests on data use validation for privacy notices within the same region [#3156](https://github.com/ethyca/fides/pull/3156)
- Improvements to export code for bugfixes and privacy declaration custom field support [#3184](https://github.com/ethyca/fides/pull/3184)
- Enabled privacy notice feature flag [#3192](https://github.com/ethyca/fides/pull/3192)
- Updated TS types - particularly with new privacy notices [#3054](https://github.com/ethyca/fides/pull/3054)
- Make name not required on privacy declaration [#3150](https://github.com/ethyca/fides/pull/3150)
- Let Rule Targets allow for custom data categories [#3147](https://github.com/ethyca/fides/pull/3147)

### Removed

- Removed the warning about access control migration [#3055](https://github.com/ethyca/fides/pull/3055)
- Remove `customFields` feature flag [#3080](https://github.com/ethyca/fides/pull/3080)
- Remove notification banner from the home page [#3088](https://github.com/ethyca/fides/pull/3088)

### Fixed

- Fix a typo in the Admin UI [#3166](https://github.com/ethyca/fides/pull/3166)
- The `--local` flag is now respected for the `scan dataset db` command [#3096](https://github.com/ethyca/fides/pull/3096)
- Fixing issue where connectors with external dataset references would fail to save [#3142](https://github.com/ethyca/fides/pull/3142)
- Ensure privacy declaration IDs are stable across updates through system API [#3188](https://github.com/ethyca/fides/pull/3188)
- Fixed unit tests for saas connector type endpoints now that we have >50 [#3101](https://github.com/ethyca/fides/pull/3101)
- Fixed nox docs link [#3121](https://github.com/ethyca/fides/pull/3121/files)

### Developer Experience

- Update fides deploy to use a new database.load_samples setting to initialize sample Systems, Datasets, and Connections for testing [#3102](https://github.com/ethyca/fides/pull/3102)
- Remove support for automatically configuring messaging (Mailgun) & storage (S3) using `.env` with `nox -s "fides_env(test)"` [#3102](https://github.com/ethyca/fides/pull/3102)
- Add smoke tests for consent management [#3158](https://github.com/ethyca/fides/pull/3158)
- Added nox command that opens dev docs [#3082](https://github.com/ethyca/fides/pull/3082)

## [2.11.0](https://github.com/ethyca/fides/compare/2.10.0...2.11.0)

### Added

- Access support for Shippo [#2484](https://github.com/ethyca/fides/pull/2484)
- Feature flags can be set such that they cannot be modified by the user [#2966](https://github.com/ethyca/fides/pull/2966)
- Added the datamap UI to make it open source [#2988](https://github.com/ethyca/fides/pull/2988)
- Introduced a `FixedLayout` component (from the datamap UI) for pages that need to be a fixed height and scroll within [#2992](https://github.com/ethyca/fides/pull/2992)
- Added preliminary privacy notice page [#2995](https://github.com/ethyca/fides/pull/2995)
- Table for privacy notices [#3001](https://github.com/ethyca/fides/pull/3001)
- Added connector template endpoint [#2946](https://github.com/ethyca/fides/pull/2946)
- Query params on connection type endpoint to filter by supported action type [#2996](https://github.com/ethyca/fides/pull/2996)
- Scope restrictions for privacy notice table in the UI [#3007](https://github.com/ethyca/fides/pull/3007)
- Toggle for enabling/disabling privacy notices in the UI [#3010](https://github.com/ethyca/fides/pull/3010)
- Add endpoint to retrieve privacy notices grouped by their associated data uses [#2956](https://github.com/ethyca/fides/pull/2956)
- Support for uploading custom connector templates via the UI [#2997](https://github.com/ethyca/fides/pull/2997)
- Add a backwards-compatible workflow for saving and propagating consent preferences with respect to Privacy Notices [#3016](https://github.com/ethyca/fides/pull/3016)
- Empty state for privacy notices [#3027](https://github.com/ethyca/fides/pull/3027)
- Added Data flow modal [#3008](https://github.com/ethyca/fides/pull/3008)
- Update datamap table export [#3038](https://github.com/ethyca/fides/pull/3038)
- Added more advanced privacy center styling [#2943](https://github.com/ethyca/fides/pull/2943)
- Backend privacy experiences foundation [#3146](https://github.com/ethyca/fides/pull/3146)

### Changed

- Set `privacyDeclarationDeprecatedFields` flags to false and set `userCannotModify` to true [2987](https://github.com/ethyca/fides/pull/2987)
- Restored `nav-config` back to the admin-ui [#2990](https://github.com/ethyca/fides/pull/2990)
- Bumped supported Python versions to 3.10.11, 3.9.16, and 3.8.14 [#2936](https://github.com/ethyca/fides/pull/2936)
- Modify privacy center default config to only request email identities, and add validation preventing requesting both email & phone identities [#2539](https://github.com/ethyca/fides/pull/2539)
- SaaS connector icons are now dynamically loaded from the connector templates [#3018](https://github.com/ethyca/fides/pull/3018)
- Updated consentmechanism Enum to rename "necessary" to "notice_only" [#3048](https://github.com/ethyca/fides/pull/3048)
- Updated test data for Mongo, CLI [#3011](https://github.com/ethyca/fides/pull/3011)
- Updated the check for if a user can assign owner roles to be scope-based instead of role-based [#2964](https://github.com/ethyca/fides/pull/2964)
- Replaced menu in user management table with delete icon [#2958](https://github.com/ethyca/fides/pull/2958)
- Added extra fields to webhook payloads [#2830](https://github.com/ethyca/fides/pull/2830)

### Removed

- Removed interzone navigation logic now that the datamap UI and admin UI are one app [#2990](https://github.com/ethyca/fides/pull/2990)
- Remove the `unknown` state for generated datasets displaying on fidesplus [#2957](https://github.com/ethyca/fides/pull/2957)
- Removed datamap export API [#2999](https://github.com/ethyca/fides/pull/2999)

### Developer Experience

- Nox commands for git tagging to support feature branch builds [#2979](https://github.com/ethyca/fides/pull/2979)
- Changed test environment (`nox -s fides_env`) to run `fides deploy` for local testing [#3071](https://github.com/ethyca/fides/pull/3017)
- Publish git-tag specific docker images [#3050](https://github.com/ethyca/fides/pull/3050)

## [2.10.0](https://github.com/ethyca/fides/compare/2.9.2...2.10.0)

### Added

- Allow users to configure their username and password via the config file [#2884](https://github.com/ethyca/fides/pull/2884)
- Add authentication to the `masking` endpoints as well as accompanying scopes [#2909](https://github.com/ethyca/fides/pull/2909)
- Add an Organization Management page (beta) [#2908](https://github.com/ethyca/fides/pull/2908)
- Adds assigned systems to user management table [#2922](https://github.com/ethyca/fides/pull/2922)
- APIs to support Privacy Notice management (create, read, update) [#2928](https://github.com/ethyca/fides/pull/2928)

### Changed

- Improved standard layout for large width screens and polished misc. pages [#2869](https://github.com/ethyca/fides/pull/2869)
- Changed UI paths in the admin-ui [#2869](https://github.com/ethyca/fides/pull/2892)
  - `/add-systems/new` --> `/add-systems/manual`
  - `/system` --> `/systems`
- Added individual ID routes for systems [#2902](https://github.com/ethyca/fides/pull/2902)
- Deprecated adding scopes to users directly; you can only add roles. [#2848](https://github.com/ethyca/fides/pull/2848/files)
- Changed About Fides page to say "Fides Core Version:" over "Version". [#2899](https://github.com/ethyca/fides/pull/2899)
- Polish Admin UI header & navigation [#2897](https://github.com/ethyca/fides/pull/2897)
- Give new users a "viewer" role by default [#2900](https://github.com/ethyca/fides/pull/2900)
- Tie together save states for user permissions and systems [#2913](https://github.com/ethyca/fides/pull/2913)
- Removing payment types from Stripe connector params [#2915](https://github.com/ethyca/fides/pull/2915)
- Viewer role can now access a restricted version of the user management page [#2933](https://github.com/ethyca/fides/pull/2933)
- Change Privacy Center email placeholder text [#2935](https://github.com/ethyca/fides/pull/2935)
- Restricted setting Approvers as System Managers [#2891](https://github.com/ethyca/fides/pull/2891)
- Adds confirmation modal when downgrading user to "approver" role via Admin UI [#2924](https://github.com/ethyca/fides/pull/2924)
- Changed the toast message for new users to include access control info [#2939](https://github.com/ethyca/fides/pull/2939)
- Add Data Stewards to datamap export [#2962](https://github.com/ethyca/fides/pull/2962)

### Fixed

- Restricted Contributors from being able to create Owners [#2888](https://github.com/ethyca/fides/pull/2888)
- Allow for dynamic aspect ratio for logo on Privacy Center 404 [#2895](https://github.com/ethyca/fides/pull/2895)
- Allow for dynamic aspect ratio for logo on consent page [#2895](https://github.com/ethyca/fides/pull/2895)
- Align role dscription drawer of Admin UI with top nav: [#2932](https://github.com/ethyca/fides/pull/2932)
- Fixed error message when a user is assigned to be an approver without any systems [#2953](https://github.com/ethyca/fides/pull/2953)

### Developer Experience

- Update frontend npm packages (admin-ui, privacy-center, cypress-e2e) [#2921](https://github.com/ethyca/fides/pull/2921)

## [2.9.2](https://github.com/ethyca/fides/compare/2.9.1...2.9.2)

### Fixed

- Allow multiple data uses as long as their processing activity name is different [#2905](https://github.com/ethyca/fides/pull/2905)
- use HTML property, not text, when dispatching Mailchimp Transactional emails [#2901](https://github.com/ethyca/fides/pull/2901)
- Remove policy key from Privacy Center submission modal [#2912](https://github.com/ethyca/fides/pull/2912)

## [2.9.1](https://github.com/ethyca/fides/compare/2.9.0...2.9.1)

### Added

- Added Attentive erasure email connector [#2782](https://github.com/ethyca/fides/pull/2782)

### Changed

- Removed dataset based email connectors [#2782](https://github.com/ethyca/fides/pull/2782)
- Changed Auth0's authentication strategy from `bearer` to `oauth2_client_credentials` [#2820](https://github.com/ethyca/fides/pull/2820)
- renamed the privacy declarations field "Privacy declaration name (deprecated)" to "Processing Activity" [#711](https://github.com/ethyca/fidesplus/issues/711)

### Fixed

- Fixed issue where the scopes list passed into FidesUserPermission could get mutated with the total_scopes call [#2883](https://github.com/ethyca/fides/pull/2883)

### Removed

- removed the `privacyDeclarationDeprecatedFields` flag [#711](https://github.com/ethyca/fidesplus/issues/711)

## [2.9.0](https://github.com/ethyca/fides/compare/2.8.3...2.9.0)

### Added

- The ability to assign users as system managers for a specific system [#2714](https://github.com/ethyca/fides/pull/2714)
- New endpoints to add and remove users as system managers [#2726](https://github.com/ethyca/fides/pull/2726)
- Warning about access control migration to the UI [#2842](https://github.com/ethyca/fides/pull/2842)
- Adds Role Assignment UI [#2739](https://github.com/ethyca/fides/pull/2739)
- Add an automated migration to give users a `viewer` role [#2821](https://github.com/ethyca/fides/pull/2821)

### Changed

- Removed "progressive" navigation that would hide Admin UI tabs until Systems / Connections were configured [#2762](https://github.com/ethyca/fides/pull/2762)
- Added `system.privacy_declaration.name` to datamap response [#2831](https://github.com/ethyca/fides/pull/2831/files)

### Developer Experience

- Retired legacy `navV2` feature flag [#2762](https://github.com/ethyca/fides/pull/2762)
- Update Admin UI Layout to fill viewport height [#2812](https://github.com/ethyca/fides/pull/2812)

### Fixed

- Fixed issue where unsaved changes warning would always show up when running fidesplus [#2788](https://github.com/ethyca/fides/issues/2788)
- Fixed problem in datamap export with datasets that had been updated via SaaS instantiation [#2841](https://github.com/ethyca/fides/pull/2841)
- Fixed problem in datamap export with inconsistent custom field ordering [#2859](https://github.com/ethyca/fides/pull/2859)

## [2.8.3](https://github.com/ethyca/fides/compare/2.8.2...2.8.3)

### Added

- Serialise `bson.ObjectId` types in SAR data packages [#2785](https://github.com/ethyca/fides/pull/2785)

### Fixed

- Fixed issue where more than 1 populated custom fields removed a system from the datamap export [#2825](https://github.com/ethyca/fides/pull/2825)

## [2.8.2](https://github.com/ethyca/fides/compare/2.8.1...2.8.2)

### Fixed

- Resolved a bug that stopped custom fields populating the visual datamap [#2775](https://github.com/ethyca/fides/pull/2775)
- Patch appconfig migration to handle existing db record [#2780](https://github.com/ethyca/fides/pull/2780)

## [2.8.1](https://github.com/ethyca/fides/compare/2.8.0...2.8.1)

### Fixed

- Disabled hiding Admin UI based on user scopes [#2771](https://github.com/ethyca/fides/pull/2771)

## [2.8.0](https://github.com/ethyca/fides/compare/2.7.1...2.8.0)

### Added

- Add API support for messaging config properties [#2551](https://github.com/ethyca/fides/pull/2551)
- Access and erasure support for Kustomer [#2520](https://github.com/ethyca/fides/pull/2520)
- Added the `erase_after` field on collections to be able to set the order for erasures [#2619](https://github.com/ethyca/fides/pull/2619)
- Add a toggle to filter the system classification to only return those with classification data [#2700](https://github.com/ethyca/fides/pull/2700)
- Added backend role-based permissions [#2671](https://github.com/ethyca/fides/pull/2671)
- Access and erasure for Vend SaaS Connector [#1869](https://github.com/ethyca/fides/issues/1869)
- Added endpoints for storage and messaging config setup status [#2690](https://github.com/ethyca/fides/pull/2690)
- Access and erasure for Jira SaaS Connector [#1871](https://github.com/ethyca/fides/issues/1871)
- Access and erasure support for Delighted [#2244](https://github.com/ethyca/fides/pull/2244)
- Improve "Upload a new dataset YAML" [#1531](https://github.com/ethyca/fides/pull/2258)
- Input validation and sanitization for Privacy Request fields [#2655](https://github.com/ethyca/fides/pull/2655)
- Access and erasure support for Yotpo [#2708](https://github.com/ethyca/fides/pull/2708)
- Custom Field Library Tab [#527](https://github.com/ethyca/fides/pull/2693)
- Allow SendGrid template usage [#2728](https://github.com/ethyca/fides/pull/2728)
- Added ConnectorRunner to simplify SaaS connector testing [#1795](https://github.com/ethyca/fides/pull/1795)
- Adds support for Mailchimp Transactional as a messaging config [#2742](https://github.com/ethyca/fides/pull/2742)

### Changed

- Admin UI
  - Add flow for selecting system types when manually creating a system [#2530](https://github.com/ethyca/fides/pull/2530)
  - Updated forms for privacy declarations [#2648](https://github.com/ethyca/fides/pull/2648)
  - Delete flow for privacy declarations [#2664](https://github.com/ethyca/fides/pull/2664)
  - Add framework to have UI elements respect the user's scopes [#2682](https://github.com/ethyca/fides/pull/2682)
  - "Manual Webhook" has been renamed to "Manual Process". [#2717](https://github.com/ethyca/fides/pull/2717)
- Convert all config values to Pydantic `Field` objects [#2613](https://github.com/ethyca/fides/pull/2613)
- Add warning to 'fides deploy' when installed outside of a virtual environment [#2641](https://github.com/ethyca/fides/pull/2641)
- Redesigned the default/init config file to be auto-documented. Also updates the `fides init` logic and analytics consent logic [#2694](https://github.com/ethyca/fides/pull/2694)
- Change how config creation/import is handled across the application [#2622](https://github.com/ethyca/fides/pull/2622)
- Update the CLI aesthetics & docstrings [#2703](https://github.com/ethyca/fides/pull/2703)
- Updates Roles->Scopes Mapping [#2744](https://github.com/ethyca/fides/pull/2744)
- Return user scopes as an enum, as well as total scopes [#2741](https://github.com/ethyca/fides/pull/2741)
- Update `MessagingServiceType` enum to be lowercased throughout [#2746](https://github.com/ethyca/fides/pull/2746)

### Developer Experience

- Set the security environment of the fides dev setup to `prod` instead of `dev` [#2588](https://github.com/ethyca/fides/pull/2588)
- Removed unexpected default Redis password [#2666](https://github.com/ethyca/fides/pull/2666)
- Privacy Center
  - Typechecking and validation of the `config.json` will be checked for backwards-compatibility. [#2661](https://github.com/ethyca/fides/pull/2661)
- Combined conftest.py files [#2669](https://github.com/ethyca/fides/pull/2669)

### Fixed

- Fix support for "redis.user" setting when authenticating to the Redis cache [#2666](https://github.com/ethyca/fides/pull/2666)
- Fix error with the classify dataset feature flag not writing the dataset to the server [#2675](https://github.com/ethyca/fides/pull/2675)
- Allow string dates to stay strings in cache decoding [#2695](https://github.com/ethyca/fides/pull/2695)
- Admin UI
  - Remove Identifiability (Data Qualifier) from taxonomy editor [2684](https://github.com/ethyca/fides/pull/2684)
- FE: Custom field selections binding issue on Taxonomy tabs [#2659](https://github.com/ethyca/fides/pull/2693/)
- Fix Privacy Request Status when submitting a consent request when identity verification is required [#2736](https://github.com/ethyca/fides/pull/2736)

## [2.7.1](https://github.com/ethyca/fides/compare/2.7.0...2.7.1)

- Fix error with the classify dataset feature flag not writing the dataset to the server [#2675](https://github.com/ethyca/fides/pull/2675)

## [2.7.0](https://github.com/ethyca/fides/compare/2.6.6...2.7.0)

- Fides API

  - Access and erasure support for Braintree [#2223](https://github.com/ethyca/fides/pull/2223)
  - Added route to send a test message [#2585](https://github.com/ethyca/fides/pull/2585)
  - Add default storage configuration functionality and associated APIs [#2438](https://github.com/ethyca/fides/pull/2438)

- Admin UI

  - Custom Metadata [#2536](https://github.com/ethyca/fides/pull/2536)
    - Create Custom Lists
    - Create Custom Field Definition
    - Create custom fields from a the taxonomy editor
    - Provide a custom field value in a resource
    - Bulk edit custom field values [#2612](https://github.com/ethyca/fides/issues/2612)
    - Custom metadata UI Polish [#2624](https://github.com/ethyca/fides/pull/2625)

- Privacy Center

  - The consent config default value can depend on whether Global Privacy Control is enabled. [#2341](https://github.com/ethyca/fides/pull/2341)
  - When GPC is enabled, the UI indicates which data uses are opted out by default. [#2596](https://github.com/ethyca/fides/pull/2596)
  - `inspectForBrowserIdentities` now also looks for `ljt_readerID`. [#2543](https://github.com/ethyca/fides/pull/2543)

### Added

- Added new Wunderkind Consent Saas Connector [#2600](https://github.com/ethyca/fides/pull/2600)
- Added new Sovrn Email Consent Connector [#2543](https://github.com/ethyca/fides/pull/2543/)
- Log Fides version at startup [#2566](https://github.com/ethyca/fides/pull/2566)

### Changed

- Update Admin UI to show all action types (access, erasure, consent, update) [#2523](https://github.com/ethyca/fides/pull/2523)
- Removes legacy `verify_oauth_client` function [#2527](https://github.com/ethyca/fides/pull/2527)
- Updated the UI for adding systems to a new design [#2490](https://github.com/ethyca/fides/pull/2490)
- Minor logging improvements [#2566](https://github.com/ethyca/fides/pull/2566)
- Various form components now take a `stacked` or `inline` variant [#2542](https://github.com/ethyca/fides/pull/2542)
- UX fixes for user management [#2537](https://github.com/ethyca/fides/pull/2537)
- Updating Firebase Auth connector to mask the user with a delete instead of an update [#2602](https://github.com/ethyca/fides/pull/2602)

### Fixed

- Fixed bug where refreshing a page in the UI would result in a 404 [#2502](https://github.com/ethyca/fides/pull/2502)
- Usernames are case insensitive now and prevent all duplicates [#2487](https://github.com/ethyca/fides/pull/2487)
  - This PR contains a migration that deletes duplicate users and keeps the oldest original account.
- Update Logos for shipped connectors [#2464](https://github.com/ethyca/fides/pull/2587)
- Search field on privacy request page isn't working [#2270](https://github.com/ethyca/fides/pull/2595)
- Fix connection dropdown in integration table to not be disabled add system creation [#3589](https://github.com/ethyca/fides/pull/3589)

### Developer Experience

- Added new Cypress E2E smoke tests [#2241](https://github.com/ethyca/fides/pull/2241)
- New command `nox -s e2e_test` which will spin up the test environment and run true E2E Cypress tests against it [#2417](https://github.com/ethyca/fides/pull/2417)
- Cypress E2E tests now run in CI and are reported to Cypress Cloud [#2417](https://github.com/ethyca/fides/pull/2417)
- Change from `randomint` to `uuid` in mongodb tests to reduce flakiness. [#2591](https://github.com/ethyca/fides/pull/2591)

### Removed

- Remove feature flagged config wizard stepper from Admin UI [#2553](https://github.com/ethyca/fides/pull/2553)

## [2.6.6](https://github.com/ethyca/fides/compare/2.6.5...2.6.6)

### Changed

- Improve Readability for Custom Masking Override Exceptions [#2593](https://github.com/ethyca/fides/pull/2593)

## [2.6.5](https://github.com/ethyca/fides/compare/2.6.4...2.6.5)

### Added

- Added config properties to override database Engine parameters [#2511](https://github.com/ethyca/fides/pull/2511)
- Increased default pool_size and max_overflow to 50 [#2560](https://github.com/ethyca/fides/pull/2560)

## [2.6.4](https://github.com/ethyca/fides/compare/2.6.3...2.6.4)

### Fixed

- Fixed bug for SMS completion notification not being sent [#2526](https://github.com/ethyca/fides/issues/2526)
- Fixed bug where refreshing a page in the UI would result in a 404 [#2502](https://github.com/ethyca/fides/pull/2502)

## [2.6.3](https://github.com/ethyca/fides/compare/2.6.2...2.6.3)

### Fixed

- Handle case where legacy dataset has meta: null [#2524](https://github.com/ethyca/fides/pull/2524)

## [2.6.2](https://github.com/ethyca/fides/compare/2.6.1...2.6.2)

### Fixed

- Issue addressing missing field in dataset migration [#2510](https://github.com/ethyca/fides/pull/2510)

## [2.6.1](https://github.com/ethyca/fides/compare/2.6.0...2.6.1)

### Fixed

- Fix errors when privacy requests execute concurrently without workers [#2489](https://github.com/ethyca/fides/pull/2489)
- Enable saas request overrides to run in worker runtime [#2489](https://github.com/ethyca/fides/pull/2489)

## [2.6.0](https://github.com/ethyca/fides/compare/2.5.1...2.6.0)

### Added

- Added the `env` option to the `security` configuration options to allow for users to completely secure the API endpoints [#2267](https://github.com/ethyca/fides/pull/2267)
- Unified Fides Resources
  - Added a dataset dropdown selector when configuring a connector to link an existing dataset to the connector configuration. [#2162](https://github.com/ethyca/fides/pull/2162)
  - Added new datasetconfig.ctl_dataset_id field to unify fides dataset resources [#2046](https://github.com/ethyca/fides/pull/2046)
- Add new connection config routes that couple them with systems [#2249](https://github.com/ethyca/fides/pull/2249)
- Add new select/deselect all permissions buttons [#2437](https://github.com/ethyca/fides/pull/2437)
- Endpoints to allow a user with the `user:password-reset` scope to reset users' passwords. In addition, users no longer require a scope to edit their own passwords. [#2373](https://github.com/ethyca/fides/pull/2373)
- New form to reset a user's password without knowing an old password [#2390](https://github.com/ethyca/fides/pull/2390)
- Approve & deny buttons on the "Request details" page. [#2473](https://github.com/ethyca/fides/pull/2473)
- Consent Propagation
  - Add the ability to execute Consent Requests via the Privacy Request Execution layer [#2125](https://github.com/ethyca/fides/pull/2125)
  - Add a Mailchimp Transactional Consent Connector [#2194](https://github.com/ethyca/fides/pull/2194)
  - Allow defining a list of opt-in and/or opt-out requests in consent connectors [#2315](https://github.com/ethyca/fides/pull/2315)
  - Add a Google Analytics Consent Connector for GA4 properties [#2302](https://github.com/ethyca/fides/pull/2302)
  - Pass the GA Cookie from the Privacy Center [#2337](https://github.com/ethyca/fides/pull/2337)
  - Rename "user_id" to more specific "ga_client_id" [#2356](https://github.com/ethyca/fides/pull/2356)
  - Patch Google Analytics Consent Connector to delete by client_id [#2355](https://github.com/ethyca/fides/pull/2355)
  - Add a "skip_param_values option" to optionally skip when we are missing param values in the body [#2384](https://github.com/ethyca/fides/pull/2384)
  - Adds a new Universal Analytics Connector that works with the UA Tracking Id
- Adds intake and storage of Global Privacy Control Signal props for Consent [#2599](https://github.com/ethyca/fides/pull/2599)

### Changed

- Unified Fides Resources
  - Removed several fidesops schemas for DSR's in favor of updated Fideslang schemas [#2009](https://github.com/ethyca/fides/pull/2009)
  - Removed DatasetConfig.dataset field [#2096](https://github.com/ethyca/fides/pull/2096)
  - Updated UI dataset config routes to use new unified routes [#2113](https://github.com/ethyca/fides/pull/2113)
  - Validate request body on crud endpoints on upsert. Validate dataset data categories before save. [#2134](https://github.com/ethyca/fides/pull/2134/)
  - Updated test env setup and quickstart to use new endpoints [#2225](https://github.com/ethyca/fides/pull/2225)
- Consent Propagation
  - Privacy Center consent options can now be marked as `executable` in order to propagate consent requests [#2193](https://github.com/ethyca/fides/pull/2193)
  - Add support for passing browser identities to consent request patches [#2304](https://github.com/ethyca/fides/pull/2304)
- Update fideslang to 1.3.3 [#2343](https://github.com/ethyca/fides/pull/2343)
- Display the request type instead of the policy name on the request table [#2382](https://github.com/ethyca/fides/pull/2382)
- Make denial reasons required [#2400](https://github.com/ethyca/fides/pull/2400)
- Display the policy key on the request details page [#2395](https://github.com/ethyca/fides/pull/2395)
- Updated CSV export [#2452](https://github.com/ethyca/fides/pull/2452)
- Privacy Request approval now uses a modal [#2443](https://github.com/ethyca/fides/pull/2443)

### Developer Experience

- `nox -s test_env` has been replaced with `nox -s "fides_env(dev)"`
- New command `nox -s "fides_env(test)"` creates a complete test environment with seed data (similar to `fides_env(dev)`) but with the production fides image so the built UI can be accessed at `localhost:8080` [#2399](https://github.com/ethyca/fides/pull/2399)
- Change from code climate to codecov for coverage reporting [#2402](https://github.com/ethyca/fides/pull/2402)

### Fixed

- Home screen header scaling and responsiveness issues [#2200](https://github.com/ethyca/fides/pull/2277)
- Privacy Center identity inputs validate even when they are optional. [#2308](https://github.com/ethyca/fides/pull/2308)
- The PII toggle defaults to false and PII will be hidden on page load [#2388](https://github.com/ethyca/fides/pull/2388)
- Fixed a CI bug caused by git security upgrades [#2441](https://github.com/ethyca/fides/pull/2441)
- Privacy Center
  - Identity inputs validate even when they are optional. [#2308](https://github.com/ethyca/fides/pull/2308)
  - Submit buttons show loading state and disable while submitting. [#2401](https://github.com/ethyca/fides/pull/2401)
  - Phone inputs no longer request country SVGs from external domain. [#2378](https://github.com/ethyca/fides/pull/2378)
  - Input validation errors no longer change the height of modals. [#2379](https://github.com/ethyca/fides/pull/2379)
- Patch masking strategies to better handle null and non-string inputs [#2307](https://github.com/ethyca/fides/pull/2377)
- Renamed prod pushes tag to be `latest` for privacy center and sample app [#2401](https://github.com/ethyca/fides/pull/2407)
- Update firebase connector to better handle non-existent users [#2439](https://github.com/ethyca/fides/pull/2439)

## [2.5.1](https://github.com/ethyca/fides/compare/2.5.0...2.5.1)

### Developer Experience

- Allow db resets only if `config.dev_mode` is `True` [#2321](https://github.com/ethyca/fides/pull/2321)

### Fixed

- Added a feature flag for the recent dataset classification UX changes [#2335](https://github.com/ethyca/fides/pull/2335)

### Security

- Add a check to the catchall path to prevent returning paths outside of the UI directory [#2330](https://github.com/ethyca/fides/pull/2330)

### Developer Experience

- Reduce size of local Docker images by fixing `.dockerignore` patterns [#2360](https://github.com/ethyca/fides/pull/2360)

## [2.5.0](https://github.com/ethyca/fides/compare/2.4.0...2.5.0)

### Docs

- Update the docs landing page and remove redundant docs [#2184](https://github.com/ethyca/fides/pull/2184)

### Added

- Added the `user` command group to the CLI. [#2153](https://github.com/ethyca/fides/pull/2153)
- Added `Code Climate` test coverage uploads. [#2198](https://github.com/ethyca/fides/pull/2198)
- Added the connection key to the execution log [#2100](https://github.com/ethyca/fides/pull/2100)
- Added endpoints to retrieve DSR `Rule`s and `Rule Target`s [#2116](https://github.com/ethyca/fides/pull/2116)
- Added Fides version number to account dropdown in the UI [#2140](https://github.com/ethyca/fides/pull/2140)
- Add link to Classify Systems page in nav side bar [#2128](https://github.com/ethyca/fides/pull/2128)
- Dataset classification UI now polls for results [#2123](https://github.com/ethyca/fides/pull/2123)
- Update Privacy Center Icons [#1800](https://github.com/ethyca/fides/pull/2139)
- Privacy Center `fides-consent.js`:
  - `Fides.shopify` integration function. [#2152](https://github.com/ethyca/fides/pull/2152)
  - Dedicated folder for integrations.
  - `Fides.meta` integration function (fbq). [#2217](https://github.com/ethyca/fides/pull/2217)
- Adds support for Twilio email service (Sendgrid) [#2154](https://github.com/ethyca/fides/pull/2154)
- Access and erasure support for Recharge [#1709](https://github.com/ethyca/fides/pull/1709)
- Access and erasure support for Friendbuy Nextgen [#2085](https://github.com/ethyca/fides/pull/2085)

### Changed

- Admin UI Feature Flags - [#2101](https://github.com/ethyca/fides/pull/2101)
  - Overrides can be saved in the browser.
  - Use `NEXT_PUBLIC_APP_ENV` for app-specific environment config.
  - No longer use `react-feature-flags` library.
  - Can have descriptions. [#2243](https://github.com/ethyca/fides/pull/2243)
- Made privacy declarations optional when adding systems manually - [#2173](https://github.com/ethyca/fides/pull/2173)
- Removed an unclear logging message. [#2266](https://github.com/ethyca/fides/pull/2266)
- Allow any user with `user:delete` scope to delete other users [#2148](https://github.com/ethyca/fides/pull/2148)
- Dynamic imports of custom overrides and SaaS test fixtures [#2169](https://github.com/ethyca/fides/pull/2169)
- Added `AuthenticatedClient` to custom request override interface [#2171](https://github.com/ethyca/fides/pull/2171)
- Only approve the specific collection instead of the entire dataset, display only top 1 classification by default [#2226](https://github.com/ethyca/fides/pull/2226)
- Update sample project resources for `fides evaluate` usage in `fides deploy` [#2253](https://github.com/ethyca/fides/pull/2253)

### Removed

- Removed unused object_name field on s3 storage config [#2133](https://github.com/ethyca/fides/pull/2133)

### Fixed

- Remove next-auth from privacy center to fix JS console error [#2090](https://github.com/ethyca/fides/pull/2090)
- Admin UI - Added Missing ability to assign `user:delete` in the permissions checkboxes [#2148](https://github.com/ethyca/fides/pull/2148)
- Nav bug: clicking on Privacy Request breadcrumb takes me to Home instead of /privacy-requests [#497](https://github.com/ethyca/fides/pull/2141)
- Side nav disappears when viewing request details [#2129](https://github.com/ethyca/fides/pull/2155)
- Remove usage of load dataset button and other dataset UI modifications [#2149](https://github.com/ethyca/fides/pull/2149)
- Improve readability for exceptions raised from custom request overrides [#2157](https://github.com/ethyca/fides/pull/2157)
- Importing custom request overrides on server startup [#2186](https://github.com/ethyca/fides/pull/2186)
- Remove warning when env vars default to blank strings in docker-compose [#2188](https://github.com/ethyca/fides/pull/2188)
- Fix Cookie House purchase modal flashing 'Error' in title [#2274](https://github.com/ethyca/fides/pull/2274)
- Stop dependency from upgrading `packaging` to version with known issue [#2273](https://github.com/ethyca/fides/pull/2273)
- Privacy center config no longer requires `identity_inputs` and will use `email` as a default [#2263](https://github.com/ethyca/fides/pull/2263)
- No longer display remaining days for privacy requests in terminal states [#2292](https://github.com/ethyca/fides/pull/2292)

### Removed

- Remove "Create New System" button when viewing systems. All systems can now be created via the "Add systems" button on the home page. [#2132](https://github.com/ethyca/fides/pull/2132)

## [2.4.0](https://github.com/ethyca/fides/compare/2.3.1...2.4.0)

### Developer Experience

- Include a pre-check workflow that collects the pytest suite [#2098](https://github.com/ethyca/fides/pull/2098)
- Write to the application db when running the app locally. Write to the test db when running pytest [#1731](https://github.com/ethyca/fides/pull/1731)

### Changed

- Move the `fides.ctl.core.` and `fides.ctl.connectors` modules into `fides.core` and `fides.connectors` respectively [#2097](https://github.com/ethyca/fides/pull/2097)
- Fides: Skip cypress tests due to nav bar 2.0 [#2102](https://github.com/ethyca/fides/pull/2103)

### Added

- Adds new erasure policy for complete user data masking [#1839](https://github.com/ethyca/fides/pull/1839)
- New Fides Home page [#1864](https://github.com/ethyca/fides/pull/2050)
- Nav 2.0 - Replace form flow side navs with top tabs [#2037](https://github.com/ethyca/fides/pull/2050)
- Adds new erasure policy for complete user data masking [#1839](https://github.com/ethyca/fides/pull/1839)
- Added ability to use Mailgun templates when sending emails. [#2039](https://github.com/ethyca/fides/pull/2039)
- Adds SMS id verification for consent [#2094](https://github.com/ethyca/fides/pull/2094)

### Fixed

- Store `fides_consent` cookie on the root domain of the Privacy Center [#2071](https://github.com/ethyca/fides/pull/2071)
- Properly set the expire-time for verification codes [#2105](https://github.com/ethyca/fides/pull/2105)

## [2.3.1](https://github.com/ethyca/fides/compare/2.3.0...2.3.1)

### Fixed

- Resolved an issue where the root_user was not being created [#2082](https://github.com/ethyca/fides/pull/2082)

### Added

- Nav redesign with sidebar groups. Feature flagged to only be visible in dev mode until release. [#2030](https://github.com/ethyca/fides/pull/2047)
- Improved error handling for incorrect app encryption key [#2089](https://github.com/ethyca/fides/pull/2089)
- Access and erasure support for Friendbuy API [#2019](https://github.com/ethyca/fides/pull/2019)

## [2.3.0](https://github.com/ethyca/fides/compare/2.2.2...2.3.0)

### Added

- Common Subscriptions for app-wide data and feature checks. [#2030](https://github.com/ethyca/fides/pull/2030)
- Send email alerts on privacy request failures once the specified threshold is reached. [#1793](https://github.com/ethyca/fides/pull/1793)
- DSR Notifications (toast) [#1895](https://github.com/ethyca/fides/pull/1895)
- DSR configure alerts btn [#1895](https://github.com/ethyca/fides/pull/1895)
- DSR configure alters (FE) [#1895](https://github.com/ethyca/fides/pull/1895)
- Add a `usage` session to Nox to print full session docstrings. [#2022](https://github.com/ethyca/fides/pull/2022)

### Added

- Adds notifications section to toml files [#2026](https://github.com/ethyca/fides/pull/2060)

### Changed

- Updated to use `loguru` logging library throughout codebase [#2031](https://github.com/ethyca/fides/pull/2031)
- Do not always create a `fides.toml` by default [#2023](https://github.com/ethyca/fides/pull/2023)
- The `fideslib` module has been merged into `fides`, code redundancies have been removed [#1859](https://github.com/ethyca/fides/pull/1859)
- Replace 'ingress' and 'egress' with 'sources' and 'destinations' across UI [#2044](https://github.com/ethyca/fides/pull/2044)
- Update the functionality of `fides pull -a <filename>` to include _all_ resource types. [#2083](https://github.com/ethyca/fides/pull/2083)

### Fixed

- Timing issues with bulk DSR reprocessing, specifically when analytics are enabled [#2015](https://github.com/ethyca/fides/pull/2015)
- Error caused by running erasure requests with disabled connectors [#2045](https://github.com/ethyca/fides/pull/2045)
- Changes the SlowAPI ratelimiter's backend to use memory instead of Redis [#2054](https://github.com/ethyca/fides/pull/2058)

## [2.2.2](https://github.com/ethyca/fides/compare/2.2.1...2.2.2)

### Docs

- Updated the readme to use new new [docs site](http://docs.ethyca.com) [#2020](https://github.com/ethyca/fides/pull/2020)

### Deprecated

- The documentation site hosted in the `/docs` directory has been deprecated. All documentation updates will be hosted at the new [docs site](http://docs.ethyca.com) [#2020](https://github.com/ethyca/fides/pull/2020)

### Fixed

- Fixed mypy and pylint errors [#2013](https://github.com/ethyca/fides/pull/2013)
- Update connection test endpoint to be effectively non-blocking [#2000](https://github.com/ethyca/fides/pull/2000)
- Update Fides connector to better handle children with no access results [#2012](https://github.com/ethyca/fides/pull/2012)

## [2.2.1](https://github.com/ethyca/fides/compare/2.2.0...2.2.1)

### Added

- Add health check indicator for data flow scanning option [#1973](https://github.com/ethyca/fides/pull/1973)

### Changed

- The `celery.toml` is no longer used, instead it is a subsection of the `fides.toml` file [#1990](https://github.com/ethyca/fides/pull/1990)
- Update sample project landing page copy to be version-agnostic [#1958](https://github.com/ethyca/fides/pull/1958)
- `get` and `ls` CLI commands now return valid `fides` object YAML [#1991](https://github.com/ethyca/fides/pull/1991)

### Developer Experience

- Remove duplicate fastapi-caching and pin version. [#1765](https://github.com/ethyca/fides/pull/1765)

## [2.2.0](https://github.com/ethyca/fides/compare/2.1.0...2.2.0)

### Added

- Send email alerts on privacy request failures once the specified threshold is reached. [#1793](https://github.com/ethyca/fides/pull/1793)
- Add authenticated privacy request route. [#1819](https://github.com/ethyca/fides/pull/1819)
- Enable the onboarding flow [#1836](https://github.com/ethyca/fides/pull/1836)
- Access and erasure support for Fullstory API [#1821](https://github.com/ethyca/fides/pull/1821)
- Add function to poll privacy request for completion [#1860](https://github.com/ethyca/fides/pull/1860)
- Added rescan flow for the data flow scanner [#1844](https://github.com/ethyca/fides/pull/1844)
- Add rescan flow for the data flow scanner [#1844](https://github.com/ethyca/fides/pull/1844)
- Add Fides connector to support parent-child Fides deployments [#1861](https://github.com/ethyca/fides/pull/1861)
- Classification UI now polls for updates to classifications [#1908](https://github.com/ethyca/fides/pull/1908)

### Changed

- The organization info form step is now skipped if the server already has organization info. [#1840](https://github.com/ethyca/fides/pull/1840)
- Removed the description column from the classify systems page. [#1867](https://github.com/ethyca/fides/pull/1867)
- Retrieve child results during fides connector execution [#1967](https://github.com/ethyca/fides/pull/1967)

### Fixed

- Fix error in parent user creation seeding. [#1832](https://github.com/ethyca/fides/issues/1832)
- Fix DSR error due to unfiltered empty identities [#1901](https://github.com/ethyca/fides/pull/1907)

### Docs

- Remove documentation about no-longer used connection string override [#1824](https://github.com/ethyca/fides/pull/1824)
- Fix typo in headings [#1824](https://github.com/ethyca/fides/pull/1824)
- Update documentation to reflect configs necessary for mailgun, twilio_sms and twilio_email service types [#1846](https://github.com/ethyca/fides/pull/1846)

...

## [2.1.0](https://github.com/ethyca/fides/compare/2.0.0...2.1.0)

### Added

- Classification flow for system data flows
- Classification is now triggered as part of data flow scanning
- Include `ingress` and `egress` fields on system export and `datamap/` endpoint [#1740](https://github.com/ethyca/fides/pull/1740)
- Repeatable unique identifier for dataset fides_keys and metadata [#1786](https://github.com/ethyca/fides/pull/1786)
- Adds SMS support for identity verification notifications [#1726](https://github.com/ethyca/fides/pull/1726)
- Added phone number validation in back-end and react phone number form in Privacy Center [#1745](https://github.com/ethyca/fides/pull/1745)
- Adds SMS message template for all subject notifications [#1743](https://github.com/ethyca/fides/pull/1743)
- Privacy-Center-Cypress workflow for CI checks of the Privacy Center. [#1722](https://github.com/ethyca/fides/pull/1722)
- Privacy Center `fides-consent.js` script for accessing consent on external pages. [Details](/clients/privacy-center/packages/fides-consent/README.md)
- Erasure support for Twilio Conversations API [#1673](https://github.com/ethyca/fides/pull/1673)
- Webserver port can now be configured via the CLI command [#1858](https://github.com/ethyca/fides/pull/1858)

### Changed

- Optional dependencies are no longer used for 3rd-party connectivity. Instead they are used to isolate dangerous dependencies. [#1679](https://github.com/ethyca/fides/pull/1679)
- All Next pages now automatically require login. [#1670](https://github.com/ethyca/fides/pull/1670)
- Running the `webserver` command no longer prompts the user to opt out/in to analytics[#1724](https://github.com/ethyca/fides/pull/1724)

### Developer Experience

- Admin-UI-Cypress tests that fail in CI will now upload screen recordings for debugging. [#1728](https://github.com/ethyca/fides/pull/1728/files/c23e62fea284f7910028c8483feff893903068b8#r1019491323)
- Enable remote debugging from VSCode of live dev app [#1780](https://github.com/ethyca/fides/pull/1780)

### Removed

- Removed the Privacy Center `cookieName` config introduced in 2.0.0. [#1756](https://github.com/ethyca/fides/pull/1756)

### Fixed

- Exceptions are no longer raised when sending analytics on Windows [#1666](https://github.com/ethyca/fides/pull/1666)
- Fixed wording on identity verification modal in the Privacy Center [#1674](https://github.com/ethyca/fides/pull/1674)
- Update system fides_key tooltip text [#1533](https://github.com/ethyca/fides/pull/1685)
- Removed local storage parsing that is redundant with redux-persist. [#1678](https://github.com/ethyca/fides/pull/1678)
- Show a helpful error message if Docker daemon is not running during "fides deploy" [#1694](https://github.com/ethyca/fides/pull/1694)
- Allow users to query their own permissions, including root user. [#1698](https://github.com/ethyca/fides/pull/1698)
- Single-select taxonomy fields legal basis and special category can be cleared. [#1712](https://github.com/ethyca/fides/pull/1712)
- Fixes the issue where the security config is not properly loading from environment variables. [#1718](https://github.com/ethyca/fides/pull/1718)
- Fixes the issue where the CLI can't run without the config values required by the webserver. [#1811](https://github.com/ethyca/fides/pull/1811)
- Correctly handle response from adobe jwt auth endpoint as milliseconds, rather than seconds. [#1754](https://github.com/ethyca/fides/pull/1754)
- Fixed styling issues with the `EditDrawer` component. [#1803](https://github.com/ethyca/fides/pull/1803)

### Security

- Bumped versions of packages that use OpenSSL [#1683](https://github.com/ethyca/fides/pull/1683)

## [2.0.0](https://github.com/ethyca/fides/compare/1.9.6...2.0.0)

### Added

- Allow delete-only SaaS connector endpoints [#1200](https://github.com/ethyca/fides/pull/1200)
- Privacy center consent choices store a browser cookie. [#1364](https://github.com/ethyca/fides/pull/1364)
  - The format is generic. A reasonable set of defaults will be added later: [#1444](https://github.com/ethyca/fides/issues/1444)
  - The cookie name defaults to `fides_consent` but can be configured under `config.json > consent > cookieName`.
  - Each consent option can provide an array of `cookieKeys`.
- Individually select and reprocess DSRs that have errored [#1203](https://github.com/ethyca/fides/pull/1489)
- Bulk select and reprocess DSRs that have errored [#1205](https://github.com/ethyca/fides/pull/1489)
- Config Wizard: AWS scan results populate in system review forms. [#1454](https://github.com/ethyca/fides/pull/1454)
- Integrate rate limiter with Saas Connectors. [#1433](https://github.com/ethyca/fides/pull/1433)
- Config Wizard: Added a column selector to the scan results page of the config wizard [#1590](https://github.com/ethyca/fides/pull/1590)
- Config Wizard: Flow for runtime scanner option [#1640](https://github.com/ethyca/fides/pull/1640)
- Access support for Twilio Conversations API [#1520](https://github.com/ethyca/fides/pull/1520)
- Message Config: Adds Twilio Email/SMS support [#1519](https://github.com/ethyca/fides/pull/1519)

### Changed

- Updated mypy to version 0.981 and Python to version 3.10.7 [#1448](https://github.com/ethyca/fides/pull/1448)

### Developer Experience

- Repository dispatch events are sent to fidesctl-plus and fidesops-plus [#1263](https://github.com/ethyca/fides/pull/1263)
- Only the `docs-authors` team members are specified as `CODEOWNERS` [#1446](https://github.com/ethyca/fides/pull/1446)
- Updates the default local configuration to not defer tasks to a worker node [#1552](https://github.com/ethyca/fides/pull/1552/)
- Updates the healthcheck to return health status of connected Celery workers [#1588](https://github.com/ethyca/fides/pull/1588)

### Docs

- Remove the tutorial to prepare for new update [#1543](https://github.com/ethyca/fides/pull/1543)
- Add system management via UI documentation [#1541](https://github.com/ethyca/fides/pull/1541)
- Added DSR quickstart docs, restructured docs navigation [#1651](https://github.com/ethyca/fides/pull/1651)
- Update privacy request execution overview docs [#1258](https://github.com/ethyca/fides/pull/1490)

### Fixed

- Fixed system dependencies appearing as "N/A" in the datamap endpoint when there are no privacy declarations [#1649](https://github.com/ethyca/fides/pull/1649)

## [1.9.6](https://github.com/ethyca/fides/compare/1.9.5...1.9.6)

### Fixed

- Include systems without a privacy declaration on data map [#1603](https://github.com/ethyca/fides/pull/1603)
- Handle malformed tokens [#1523](https://github.com/ethyca/fides/pull/1523)
- Remove thrown exception from getAllPrivacyRequests method [#1592](https://github.com/ethyca/fides/pull/1593)
- Include systems without a privacy declaration on data map [#1603](https://github.com/ethyca/fides/pull/1603)
- After editing a dataset, the table will stay on the previously selected collection instead of resetting to the first one. [#1511](https://github.com/ethyca/fides/pull/1511)
- Fix redis `db_index` config issue [#1647](https://github.com/ethyca/fides/pull/1647)

### Docs

- Add unlinked docs and fix any remaining broken links [#1266](https://github.com/ethyca/fides/pull/1266)
- Update privacy center docs to include consent information [#1537](https://github.com/ethyca/fides/pull/1537)
- Update UI docs to include DSR countdown information and additional descriptions/filtering [#1545](https://github.com/ethyca/fides/pull/1545)

### Changed

- Allow multiple masking strategies to be specified when using fides as a masking engine [#1647](https://github.com/ethyca/fides/pull/1647)

## [1.9.5](https://github.com/ethyca/fides/compare/1.9.4...1.9.5)

### Added

- The database includes a `plus_system_scans` relation, to track the status and results of System Scanner executions in fidesctl-plus [#1554](https://github.com/ethyca/fides/pull/1554)

## [1.9.4](https://github.com/ethyca/fides/compare/1.9.2...1.9.4)

### Fixed

- After editing a dataset, the table will stay on the previously selected collection instead of resetting to the first one. [#1511](https://github.com/ethyca/fides/pull/1511)

## [1.9.2](https://github.com/ethyca/fides/compare/1.9.1...1.9.2)

### Deprecated

- Added a deprecation warning for the entire package [#1244](https://github.com/ethyca/fides/pull/1244)

### Added

- Dataset generation enhancements using Fides Classify for Plus users:

  - Integrate Fides Plus API into placeholder features introduced in 1.9.0. [#1194](https://github.com/ethyca/fides/pull/1194)

- Fides Admin UI:

  - Configure Connector after creation [#1204](https://github.com/ethyca/fides/pull/1356)

### Fixed

- Privacy Center:
  - Handle error on startup if server isn't running [#1239](https://github.com/ethyca/fides/pull/1239)
  - Fix styling issue with cards [#1240](https://github.com/ethyca/fides/pull/1240)
  - Redirect to index on consent save [#1238](https://github.com/ethyca/fides/pull/1238)

## [1.9.1](https://github.com/ethyca/fides/compare/1.9.0...1.9.1)

### Changed

- Update fideslang to v1.3.1 [#1136](https://github.com/ethyca/fides/pull/1136)

### Changed

- Update fideslang to v1.3.1 [#1136](https://github.com/ethyca/fides/pull/1136)

## [1.9.0](https://github.com/ethyca/fides/compare/1.8.6...1.9.0) - 2022-09-29

### Added

- Dataset generation enhancements using Fides Classify for Plus users:
  - Added toggle for enabling classify during generation. [#1057](https://github.com/ethyca/fides/pull/1057)
  - Initial implementation of API request to kick off classify, with confirmation modal. [#1069](https://github.com/ethyca/fides/pull/1069)
  - Initial Classification & Review status for generated datasets. [#1074](https://github.com/ethyca/fides/pull/1074)
  - Component for choosing data categories based on classification results. [#1110](https://github.com/ethyca/fides/pull/1110)
  - The dataset fields table shows data categories from the classifier (if available). [#1088](https://github.com/ethyca/fides/pull/1088)
  - The "Approve" button can be used to update the dataset with the classifier's suggestions. [#1129](https://github.com/ethyca/fides/pull/1129)
- System management UI:
  - New page to add a system via yaml [#1062](https://github.com/ethyca/fides/pull/1062)
  - Skeleton of page to add a system manually [#1068](https://github.com/ethyca/fides/pull/1068)
  - Refactor config wizard system forms to be reused for system management [#1072](https://github.com/ethyca/fides/pull/1072)
  - Add additional optional fields to system management forms [#1082](https://github.com/ethyca/fides/pull/1082)
  - Delete a system through the UI [#1085](https://github.com/ethyca/fides/pull/1085)
  - Edit a system through the UI [#1096](https://github.com/ethyca/fides/pull/1096)
- Cypress component testing [#1106](https://github.com/ethyca/fides/pull/1106)

### Changed

- Changed behavior of `load_default_taxonomy` to append instead of upsert [#1040](https://github.com/ethyca/fides/pull/1040)
- Changed behavior of adding privacy declarations to decouple the actions of the "add" and "next" buttons [#1086](https://github.com/ethyca/fides/pull/1086)
- Moved system related UI components from the `config-wizard` directory to the `system` directory [#1097](https://github.com/ethyca/fides/pull/1097)
- Updated "type" on SaaS config to be a simple string type, not an enum [#1197](https://github.com/ethyca/fides/pull/1197)

### Developer Experience

- Optional dependencies may have their version defined only once, in `optional-requirements.txt` [#1171](https://github.com/ethyca/fides/pull/1171)

### Docs

- Updated the footer links [#1130](https://github.com/ethyca/fides/pull/1130)

### Fixed

- Fixed the "help" link in the UI header [#1078](https://github.com/ethyca/fides/pull/1078)
- Fixed a bug in Data Category Dropdowns where checking i.e. `user.biometric` would also check `user.biometric_health` [#1126](https://github.com/ethyca/fides/pull/1126)

### Security

- Upgraded pymysql to version `1.0.2` [#1094](https://github.com/ethyca/fides/pull/1094)

## [1.8.6](https://github.com/ethyca/fides/compare/1.8.5...1.8.6) - 2022-09-28

### Added

- Added classification tables for Plus users [#1060](https://github.com/ethyca/fides/pull/1060)

### Fixed

- Fixed a bug where rows were being excluded from a data map [#1124](https://github.com/ethyca/fides/pull/1124)

## [1.8.5](https://github.com/ethyca/fides/compare/1.8.4...1.8.5) - 2022-09-21

### Changed

- Update fideslang to v1.3.0 [#1103](https://github.com/ethyca/fides/pull/1103)

## [1.8.4](https://github.com/ethyca/fides/compare/1.8.3...1.8.4) - 2022-09-09

### Added

- Initial system management page [#1054](https://github.com/ethyca/fides/pull/1054)

### Changed

- Deleting a taxonomy field with children will now cascade delete all of its children as well. [#1042](https://github.com/ethyca/fides/pull/1042)

### Fixed

- Fixed navigating directly to frontend routes loading index page instead of the correct static page for the route.
- Fix truncated evaluation error messages [#1053](https://github.com/ethyca/fides/pull/1053)

## [1.8.3](https://github.com/ethyca/fides/compare/1.8.2...1.8.3) - 2022-09-06

### Added

- Added more taxonomy fields that can be edited via the UI [#1000](https://github.com/ethyca/fides/pull/1000) [#1028](https://github.com/ethyca/fides/pull/1028)
- Added the ability to add taxonomy fields via the UI [#1019](https://github.com/ethyca/fides/pull/1019)
- Added the ability to delete taxonomy fields via the UI [#1006](https://github.com/ethyca/fides/pull/1006)
  - Only non-default taxonomy entities can be deleted [#1023](https://github.com/ethyca/fides/pull/1023)
- Prevent deleting taxonomy `is_default` fields and from adding `is_default=True` fields via the API [#990](https://github.com/ethyca/fides/pull/990).
- Added a "Custom" tag to distinguish user defined taxonomy fields from default taxonomy fields in the UI [#1027](https://github.com/ethyca/fides/pull/1027)
- Added initial support for enabling Fides Plus [#1037](https://github.com/ethyca/fides/pull/1037)
  - The `useFeatures` hook can be used to check if `plus` is enabled.
  - Navigating to/from the Data Map page is gated behind this feature.
  - Plus endpoints are served from the private Plus image.

### Fixed

- Fixed failing mypy tests [#1030](https://github.com/ethyca/fides/pull/1030)
- Fixed an issue where `fides push --diff` would return a false positive diff [#1026](https://github.com/ethyca/fides/pull/1026)
- Pinned pydantic version to < 1.10.0 to fix an error in finding referenced fides keys [#1045](https://github.com/ethyca/fides/pull/1045)

### Fixed

- Fixed failing mypy tests [#1030](https://github.com/ethyca/fides/pull/1030)
- Fixed an issue where `fides push --diff` would return a false positive diff [#1026](https://github.com/ethyca/fides/pull/1026)

### Docs

- Minor formatting updates to [Policy Webhooks](https://ethyca.github.io/fidesops/guides/policy_webhooks/) documentation [#1114](https://github.com/ethyca/fidesops/pull/1114)

### Removed

- Removed create superuser [#1116](https://github.com/ethyca/fidesops/pull/1116)

## [1.8.2](https://github.com/ethyca/fides/compare/1.8.1...1.8.2) - 2022-08-18

### Added

- Added the ability to edit taxonomy fields via the UI [#977](https://github.com/ethyca/fides/pull/977) [#1028](https://github.com/ethyca/fides/pull/1028)
- New column `is_default` added to DataCategory, DataUse, DataSubject, and DataQualifier tables [#976](https://github.com/ethyca/fides/pull/976)
- Added the ability to add taxonomy fields via the UI [#1019](https://github.com/ethyca/fides/pull/1019)
- Added the ability to delete taxonomy fields via the UI [#1006](https://github.com/ethyca/fides/pull/1006)
  - Only non-default taxonomy entities can be deleted [#1023](https://github.com/ethyca/fides/pull/1023)
- Prevent deleting taxonomy `is_default` fields and from adding `is_default=True` fields via the API [#990](https://github.com/ethyca/fides/pull/990).
- Added a "Custom" tag to distinguish user defined taxonomy fields from default taxonomy fields in the UI [#1027](https://github.com/ethyca/fides/pull/1027)

### Changed

- Upgraded base Docker version to Python 3.9 and updated all other references from 3.8 -> 3.9 [#974](https://github.com/ethyca/fides/pull/974)
- Prepend all database tables with `ctl_` [#979](https://github.com/ethyca/fides/pull/979)
- Moved the `admin-ui` code down one level into a `ctl` subdir [#970](https://github.com/ethyca/fides/pull/970)
- Extended the `/datamap` endpoint to include extra metadata [#992](https://github.com/ethyca/fides/pull/992)

## [1.8.1](https://github.com/ethyca/fides/compare/1.8.0...1.8.1) - 2022-08-08

### Deprecated

- The following environment variables have been deprecated, and replaced with the new environment variable names indicated below. To avoid breaking existing workflows, the deprecated variables are still respected in v1.8.1. They will be removed in a future release.
  - `FIDESCTL__API__DATABASE_HOST` --> `FIDESCTL__DATABASE__SERVER`
  - `FIDESCTL__API__DATABASE_NAME` --> `FIDESCTL__DATABASE__DB`
  - `FIDESCTL__API__DATABASE_PASSWORD` --> `FIDESCTL__DATABASE__PASSWORD`
  - `FIDESCTL__API__DATABASE_PORT` --> `FIDESCTL__DATABASE__PORT`
  - `FIDESCTL__API__DATABASE_TEST_DATABASE_NAME` --> `FIDESCTL__DATABASE__TEST_DB`
  - `FIDESCTL__API__DATABASE_USER` --> `FIDESCTL__DATABASE__USER`

### Developer Experience

- The included `docker-compose.yml` no longer references outdated ENV variables [#964](https://github.com/ethyca/fides/pull/964)

### Docs

- Minor release documentation now reflects the desired patch release process [#955](https://github.com/ethyca/fides/pull/955)
- Updated references to ENV variables [#964](https://github.com/ethyca/fides/pull/964)

### Fixed

- Deprecated config options will continue to be respected when set via environment variables [#965](https://github.com/ethyca/fides/pull/965)
- The git cache is rebuilt within the Docker container [#962](https://github.com/ethyca/fides/pull/962)
- The `wheel` pypi build no longer has a dirty version tag [#962](https://github.com/ethyca/fides/pull/962)
- Add setuptools to dev-requirements to fix versioneer error [#983](https://github.com/ethyca/fides/pull/983)

## [1.8.0](https://github.com/ethyca/fides/compare/1.7.1...1.8.0) - 2022-08-04

### Added

- Initial configuration wizard UI view
  - System scanning step: AWS credentials form and initial `generate` API usage.
  - System scanning results: AWS systems are stored and can be selected for review
- CustomInput type "password" with show/hide icon.
- Pull CLI command now checks for untracked/unstaged files in the manifests dir [#869](https://github.com/ethyca/fides/pull/869)
- Pull CLI command has a flag to pull missing files from the server [#895](https://github.com/ethyca/fides/pull/895)
- Add BigQuery support for the `generate` command and `/generate` endpoint [#814](https://github.com/ethyca/fides/pull/814) & [#917](https://github.com/ethyca/fides/pull/917)
- Added user auth tables [915](https://github.com/ethyca/fides/pull/915)
- Standardized API error parsing under `~/types/errors`
- Added taxonomy page to UI [#902](https://github.com/ethyca/fides/pull/902)
  - Added a nested accordion component for displaying taxonomy data [#910](https://github.com/ethyca/fides/pull/910)
- Add lru cache to get_config [927](https://github.com/ethyca/fides/pull/927)
- Add support for deprecated API config values [#959](https://github.com/ethyca/fides/pull/959)
- `fides` is now an alias for `fidesctl` as a CLI entrypoint [#926](https://github.com/ethyca/fides/pull/926)
- Add user auth routes [929](https://github.com/ethyca/fides/pull/929)
- Bump fideslib to 3.0.1 and remove patch code[931](https://github.com/ethyca/fides/pull/931)
- Update the `fidesctl` python package to automatically serve the UI [#941](https://github.com/ethyca/fides/pull/941)
- Add `push` cli command alias for `apply` and deprecate `apply` [943](https://github.com/ethyca/fides/pull/943)
- Add resource groups tagging api as a source of system generation [939](https://github.com/ethyca/fides/pull/939)
- Add GitHub Action to publish the `fidesctl` package to testpypi on pushes to main [#951](https://github.com/ethyca/fides/pull/951)
- Added configWizardFlag to ui to hide the config wizard when false [[#1453](https://github.com/ethyca/fides/issues/1453)

### Changed

- Updated the `datamap` endpoint to return human-readable column names as the first response item [#779](https://github.com/ethyca/fides/pull/779)
- Remove the `obscure` requirement from the `generate` endpoint [#819](https://github.com/ethyca/fides/pull/819)
- Moved all files from `fidesapi` to `fidesctl/api` [#885](https://github.com/ethyca/fides/pull/885)
- Moved `scan` and `generate` to the list of commands that can be run in local mode [#841](https://github.com/ethyca/fides/pull/841)
- Upgraded the base docker images from Debian Buster to Bullseye [#958](https://github.com/ethyca/fides/pull/958)
- Removed `ipython` as a dev-requirement [#958](https://github.com/ethyca/fides/pull/958)
- Webserver dependencies now come as a standard part of the package [#881](https://github.com/ethyca/fides/pull/881)
- Initial configuration wizard UI view
  - Refactored step & form results management to use Redux Toolkit slice.
- Change `id` field in tables from an integer to a string [915](https://github.com/ethyca/fides/pull/915)
- Update `fideslang` to `1.1.0`, simplifying the default taxonomy and adding `tags` for resources [#865](https://github.com/ethyca/fides/pull/865)
- Merge existing configurations with `fideslib` library [#913](https://github.com/ethyca/fides/pull/913)
- Moved frontend static files to `src/fidesctl/ui-build/static` [#934](https://github.com/ethyca/fides/pull/934)
- Replicated the error response handling from the `/validate` endpoint to the `/generate` endpoint [#911](https://github.com/ethyca/fides/pull/911)

### Developer Experience

- Remove `API_PREFIX` from fidesctl/core/utils.py and change references to `API_PREFIX` in fidesctl/api/reoutes/util.py [922](https://github.com/ethyca/fides/pull/922)

### Fixed

- Dataset field columns show all columns by default in the UI [#898](https://github.com/ethyca/fides/pull/898)
- Fixed the missing `.fides./` directory when locating the default config [#933](https://github.com/ethyca/fides/pull/933)

## [1.7.1](https://github.com/ethyca/fides/compare/1.7.0...1.7.1) - 2022-07-28

### Added

- Add datasets via YAML in the UI [#813](https://github.com/ethyca/fides/pull/813)
- Add datasets via database connection [#834](https://github.com/ethyca/fides/pull/834) [#889](https://github.com/ethyca/fides/pull/889)
- Add delete confirmation when deleting a field or collection from a dataset [#809](https://github.com/ethyca/fides/pull/809)
- Add ability to delete datasets from the UI [#827](https://github.com/ethyca/fides/pull/827)
- Add Cypress for testing [713](https://github.com/ethyca/fides/pull/833)
- Add datasets via database connection (UI only) [#834](https://github.com/ethyca/fides/pull/834)
- Add Okta support to the `/generate` endpoint [#842](https://github.com/ethyca/fides/pull/842)
- Add db support to `/generate` endpoint [849](https://github.com/ethyca/fides/pull/849)
- Added OpenAPI TypeScript client generation for the UI app. See the [README](/clients/admin-ui/src/types/api/README.md) for more details.

### Changed

- Remove the `obscure` requirement from the `generate` endpoint [#819](https://github.com/ethyca/fides/pull/819)

### Developer Experience

- When releases are published, dispatch a repository webhook event to ethyca/fidesctl-plus [#938](https://github.com/ethyca/fides/pull/938)

### Docs

- recommend/replace pip installs with pipx [#874](https://github.com/ethyca/fides/pull/874)

### Fixed

- CustomSelect input tooltips appear next to selector instead of wrapping to a new row.
- Datasets without the `third_country_transfer` will not cause the editing dataset form to not render.
- Fixed a build issue causing an `unknown` version of `fidesctl` to be installed in published Docker images [#836](https://github.com/ethyca/fides/pull/836)
- Fixed an M1-related SQLAlchemy bug [#816](https://github.com/ethyca/fides/pull/891)
- Endpoints now work with or without a trailing slash. [#886](https://github.com/ethyca/fides/pull/886)
- Dataset field columns show all columns by default in the UI [#898](https://github.com/ethyca/fides/pull/898)
- Fixed the `tag` specific GitHub Action workflows for Docker and publishing docs. [#901](https://github.com/ethyca/fides/pull/901)

## [1.7.0](https://github.com/ethyca/fides/compare/1.6.1...1.7.0) - 2022-06-23

### Added

- Added dependabot to keep dependencies updated
- A warning now issues for any orphan datasets as part of the `apply` command [543](https://github.com/ethyca/fides/pull/543)
- Initial scaffolding of management UI [#561](https://github.com/ethyca/fides/pull/624)
- A new `audit` command for `system` and `organization` resources, checking data map attribute compliance [#548](https://github.com/ethyca/fides/pull/548)
- Static UI assets are now built with the docker container [#663](https://github.com/ethyca/fides/issues/663)
- Host static files via fidesapi [#621](https://github.com/ethyca/fides/pull/621)
- A new `generate` endpoint to enable capturing systems from infrastructure from the UI [#642](https://github.com/ethyca/fides/pull/642)
- A new `datamap` endpoint to enable visualizing a data map from the UI [#721](https://github.com/ethyca/fides/pull/721)
- Management UI navigation bar [#679](https://github.com/ethyca/fides/issues/679)
- Management UI integration [#736](https://github.com/ethyca/fides/pull/736)
  - Datasets
  - Systems
  - Taxonomy (data categories)
- Initial dataset UI view [#768](https://github.com/ethyca/fides/pull/768)
  - Add interaction for viewing a dataset collection
  - Add column picker
  - Add a data category checklist tree
  - Edit/delete dataset fields
  - Edit/delete dataset collections
  - Edit datasets
  - Add a component for Identifiability tags
  - Add tooltips for help on forms
  - Add geographic location (third_country_transfers) country selection. Supported by new dependency `i18n-iso-countries`.
- Okta, aws and database credentials can now come from `fidesctl.toml` config [#694](https://github.com/ethyca/fides/pull/694)
- New `validate` endpoint to test aws and okta credentials [#722](https://github.com/ethyca/fides/pull/722)
- Initial configuration wizard UI view
  - Manual entry steps added (name and describe organization, pick entry route, and describe system manually including privacy declarations)
- A new image tagged `ethyca/fidesctl:dev` is published on each push to `main` [781](https://github.com/ethyca/fides/pull/781)
- A new cli command (`fidesctl sync`) [#765](https://github.com/ethyca/fides/pull/765)

### Changed

- Comparing server and CLI versions ignores `.dirty` only differences, and is quiet on success when running general CLI commands [621](https://github.com/ethyca/fides/pull/621)
- All endpoints now prefixed by `/api/v1` [#623](https://github.com/ethyca/fides/issues/623)
- Allow AWS credentials to be passed to `generate system` via the API [#645](https://github.com/ethyca/fides/pull/645)
- Update the export of a datamap to load resources from the server instead of a manifest directory [#662](https://github.com/ethyca/fides/pull/662)
- Refactor `export` to remove CLI specific uses from the core modules and load resources[#725](https://github.com/ethyca/fides/pull/725)
- Bump version of FastAPI in `setup.py` to 0.77.1 to match `optional-requirements.txt` [#734](https://github.com/ethyca/fides/pull/734)
- Docker images are now only built and pushed on tags to match when released to pypi [#740](https://github.com/ethyca/fides/pull/740)
- Okta resource scanning and generation now works with systems instead of datasets [#751](https://github.com/ethyca/fides/pull/751)

### Developer Experience

- Replaced `make` with `nox` [#547](https://github.com/ethyca/fides/pull/547)
- Removed usage of `fideslang` module in favor of new [external package](https://github.com/ethyca/fideslang) shared across projects [#619](https://github.com/ethyca/fides/issues/619)
- Added a UI service to the docker-compose deployment [#757](https://github.com/ethyca/fides/pull/757)
- `TestClient` defined in and shared across test modules via `conftest.py` [#759](https://github.com/ethyca/fides/pull/759)

### Docs

- Replaced all references to `make` with `nox` [#547](https://github.com/ethyca/fides/pull/547)
- Removed config/schemas page [#613](https://github.com/ethyca/fides/issues/613)
- Dataset UI and config wizard docs added ([https://github.com/ethyca/fides/pull/697](https://github.com/ethyca/fides/pull/697))
- The fides README now walks through generating a datamap [#746](https://github.com/ethyca/fides/pull/746)

### Fixed

- Updated `fideslog` to v1.1.5, resolving an issue where some exceptions thrown by the SDK were not handled as expected [#609](https://github.com/ethyca/fides/issues/609)
- Updated the webserver so that it won't fail if the database is inaccessible [#649](https://github.com/ethyca/fides/pull/649)
- Updated external tests to handle complex characters [#661](https://github.com/ethyca/fides/pull/661)
- Evaluations now properly merge the default taxonomy into the user-defined taxonomy [#684](https://github.com/ethyca/fides/pull/684)
- The CLI can now be run without installing the webserver components [#715](https://github.com/ethyca/fides/pull/715)

## [1.6.1](https://github.com/ethyca/fides/compare/1.6.0...1.6.1) - 2022-06-15

### Docs

- Updated `Release Steps`

### Fixed

- Resolved a failure with populating applicable data subject rights to a data map
- Handle invalid characters when generating a `fides_key` [#761](https://github.com/ethyca/fides/pull/761)

## [1.6.0](https://github.com/ethyca/fides/compare/1.5.3...1.6.0) - 2022-05-02

### Added

- ESLint configuration changes [#514](https://github.com/ethyca/fidesops/pull/514)
- User creation, update and permissions in the Admin UI [#511](https://github.com/ethyca/fidesops/pull/511)
- Yaml support for dataset upload [#284](https://github.com/ethyca/fidesops/pull/284)

### Breaking Changes

- Update masking API to take multiple input values [#443](https://github.com/ethyca/fidesops/pull/443)

### Docs

- DRP feature documentation [#520](https://github.com/ethyca/fidesops/pull/520)

## [1.4.2](https://github.com/ethyca/fidesops/compare/1.4.1...1.4.2) - 2022-05-12

### Added

- GET routes for users [#405](https://github.com/ethyca/fidesops/pull/405)
- Username based search on GET route [#444](https://github.com/ethyca/fidesops/pull/444)
- FIDESOPS\_\_DEV_MODE for Easier SaaS Request Debugging [#363](https://github.com/ethyca/fidesops/pull/363)
- Track user privileges across sessions [#425](https://github.com/ethyca/fidesops/pull/425)
- Add first_name and last_name fields. Also add them along with created_at to FidesUser response [#465](https://github.com/ethyca/fidesops/pull/465)
- Denial reasons for DSR and user `AuditLog` [#463](https://github.com/ethyca/fidesops/pull/463)
- DRP action to Policy [#453](https://github.com/ethyca/fidesops/pull/453)
- `CHANGELOG.md` file[#484](https://github.com/ethyca/fidesops/pull/484)
- DRP status endpoint [#485](https://github.com/ethyca/fidesops/pull/485)
- DRP exerise endpoint [#496](https://github.com/ethyca/fidesops/pull/496)
- Frontend for privacy request denial reaons [#480](https://github.com/ethyca/fidesops/pull/480)
- Publish Fidesops to Pypi [#491](https://github.com/ethyca/fidesops/pull/491)
- DRP data rights endpoint [#526](https://github.com/ethyca/fidesops/pull/526)

### Changed

- Converted HTTP Status Codes to Starlette constant values [#438](https://github.com/ethyca/fidesops/pull/438)
- SaasConnector.send behavior on ignore_errors now returns raw response [#462](https://github.com/ethyca/fidesops/pull/462)
- Seed user permissions in `create_superuser.py` script [#468](https://github.com/ethyca/fidesops/pull/468)
- User API Endpoints (update fields and reset user passwords) [#471](https://github.com/ethyca/fidesops/pull/471)
- Format tests with `black` [#466](https://github.com/ethyca/fidesops/pull/466)
- Extract privacy request endpoint logic into separate service for DRP [#470](https://github.com/ethyca/fidesops/pull/470)
- Fixing inconsistent SaaS connector integration tests [#473](https://github.com/ethyca/fidesops/pull/473)
- Add user data to login response [#501](https://github.com/ethyca/fidesops/pull/501)

### Breaking Changes

- Update masking API to take multiple input values [#443](https://github.com/ethyca/fidesops/pull/443)

### Docs

- Added issue template for documentation updates [#442](https://github.com/ethyca/fidesops/pull/442)
- Clarify masking updates [#464](https://github.com/ethyca/fidesops/pull/464)
- Added dark mode [#476](https://github.com/ethyca/fidesops/pull/476)

### Fixed

- Removed miradb test warning [#436](https://github.com/ethyca/fidesops/pull/436)
- Added missing import [#448](https://github.com/ethyca/fidesops/pull/448)
- Removed pypi badge pointing to wrong package [#452](https://github.com/ethyca/fidesops/pull/452)
- Audit imports and references [#479](https://github.com/ethyca/fidesops/pull/479)
- Switch to using update method on PUT permission endpoint [#500](https://github.com/ethyca/fidesops/pull/500)

### Developer Experience

- added isort as a CI check
- Include `tests/` in all static code checks (e.g. `mypy`, `pylint`)

### Changed

- Published Docker image does a clean install of Fidesctl
- `with_analytics` is now a decorator

### Fixed

- Third-Country formatting on Data Map
- Potential Duplication on Data Map
- Exceptions are no longer raised when sending `AnalyticsEvent`s on Windows
- Running `fidesctl init` now generates a `server_host` and `server_protocol`
  rather than `server_url`
