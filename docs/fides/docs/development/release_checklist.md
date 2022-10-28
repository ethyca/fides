# Release Checklist

The release checklist is a manual set of checks done before each release to ensure functionality of the most critical components of the application. Some of these steps are redundant with automated tests, while others are _only_ tested here as part of this check.

This checklist can be copy/pasted into the final pre-release PR.

## General

- [ ] Quickstart verified working and up-to-date
- [ ] New tables/columns added to database diagram
- [ ] `nox -s test_env` works (verify the admin UI, privacy center, CLI and webserver)
- [ ] `fides deploy` works (verify the admin UI, privacy center, CLI and webserver)

## API

- [ ] Verify that the generated API docs are correct
- [ ] Verify that the Postman collection has been updated

## CLI

- [ ] do a push
- [ ] do a pull
- [ ] Run a local evaluation
- [ ] Run an evaluation
- [ ] Scan a database
- [ ] generate a database

## Admin UI

- [ ] Every navigation button works
- [ ] DSR approval succeeds
- [ ] DSR execution succeeds

## Privacy Center

- [ ] Every navigation button works
- [ ] DSR submission succeeds
- [ ] Consent request submission succeeds

## Documentation

- [ ] Verify that the CHANGELOG is formatted correctly and clean up verbiage where needed
- [ ] Verify that the CHANGELOG is representative of the actual changes
