# Release Checklist

The release checklist is a manual set of checks done before each release to ensure functionality of the most critical components of the application. Some of these steps are redundant with automated tests, while others are _only_ tested here as part of this check.

This checklist can be copy/pasted into the final pre-release PR.

## General

- [ ] Quickstart verified working and up-to-date
- [ ] New tables/columns added to database diagram

## API

- [ ] Verify that the generated API docs are correct
- [ ] Verify that the Postman collection has been updated

## CLI

- [ ] Run a local evaluation
- [ ] Run a standard evaluation
- [ ] Scan the database

## Admin UI

- [ ] Every navigation button works

## Privacy Center

- [ ] Every navigation button works

## Documentation

- [ ] Verify that the changelog
