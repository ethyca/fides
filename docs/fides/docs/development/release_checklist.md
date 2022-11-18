# Release Checklist

The release checklist is a manual set of checks done before each release to ensure functionality of the most critical components of the application. Some of these steps are redundant with automated tests, while others are _only_ tested here as part of this check.

This checklist should be copy/pasted into the final pre-release PR, and checked off as you complete each step.

## Pre-Release Steps

### General

- [ ] Quickstart verified working and up-to-date
- [ ] New tables/columns added to database diagram
- [ ] `nox -s test_env` works (verify the admin UI, privacy center, CLI and webserver)
- [ ] `fides deploy up` works (verify the admin UI, privacy center, CLI and webserver)

### API

- [ ] Verify that the generated API docs are correct
- [ ] Verify that the Postman collection has been updated

### CLI

- [ ] Run a `fides push`
- [ ] Run a `fides pull`
- [ ] Run a `fides evaluate`
- [ ] Generate a dataset with `fides generate dataset db`
- [ ] Scan a database with `fides scan dataset db`

### Admin UI

- [ ] Every navigation button works
- [ ] DSR approval succeeds
- [ ] DSR execution succeeds

### Privacy Center

- [ ] Every navigation button works
- [ ] DSR submission succeeds
- [ ] Consent request submission succeeds

### Documentation

- [ ] Verify that the CHANGELOG is formatted correctly and clean up verbiage where needed
- [ ] Verify that the CHANGELOG is representative of the actual changes

## Post-Release Steps

- [ ] Verify the ethyca-fides release is published to PyPi: https://pypi.org/project/ethyca-fides/#history
- [ ] Verify the fides release is published to DockerHub: https://hub.docker.com/r/ethyca/fides
- [ ] Verify the fides-privacy-center release is published to DockerHub: https://hub.docker.com/r/ethyca/fides-privacy-center
- [ ] Verify the fides-sample-app release is published to DockerHub: https://hub.docker.com/r/ethyca/fides-sample-app
- [ ] Smoke test the PyPi & DockerHub releases with a clean `pip install ethyca-fides` and `fides deploy up`
