# Release Checklist

The release checklist is a manual set of checks done before each release to ensure functionality of the most critical components of the application. Some of these steps are redundant with automated tests, while others are _only_ tested here as part of this check.

This checklist should be copy/pasted into the final pre-release PR, and checked off as you complete each step.

## Pre-Release Steps

### General

- [ ] Quickstart verified working and up-to-date
- [ ] Add any new tables/columns to the [database diagram](https://github.com/ethyca/fides/blob/5a485387d8af247ec6479e4115088cbbb8394d77/docs/fides/docs/development/update_erd_diagram.md) if they have not already been added
  - To check for the new tables/columns that have been added in the release, look for new migration files in the `src/fides/api/ctl/migrations` directory and inspect their contents
  - If found, look at the latest database diagram, and check whether it contains the tables/columns that were added in these migrations
  - If the diagram is not up to date, follow the steps in the link above to generate a new database diagram with the up-to-date schema, ensuring that all tables and their relationships can be clearly seen
  - Open up an issue on [fidesdocs](https://github.com/ethyca/fidesdocs/issues) to update the diagram on the new docs site
- [ ] `nox -s test_env` works (verify the admin UI, privacy center, CLI and webserver)
- [ ] `nox -s "build(sample)"` works on the release branch, creating the sample images (this is also prereq for `fides deploy up`)
- [ ] `fides deploy up --no-pull` works using the images built in previous step (verify the admin UI, privacy center, CLI and webserver)

```
mkdir ~/fides-2-1-0-test
cd ~/fides-2-1-0-test
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/ethyca/fides.git@<branch>
fides deploy up --no-pull
fides status
fides deploy down
rm -rf ~/fides-2-1-0-test
exit
```

Next, run the following checks against the environment you've spun up using `fides deploy up --no-pull`:

### API

- [ ] Verify that the generated API docs are correct
- [ ] Verify that the [Postman collection](https://github.com/ethyca/fides/blob/main/docs/fides/docs/development/postman/Fides.postman_collection.json) has been updated

### CLI

Run these from within `nox -s dev -- shell`

- [ ] Run a `fides push`
- [ ] Run a `fides pull`
- [ ] Run a `fides evaluate`
- [ ] Generate a dataset with `fides generate dataset db --credentials-id app_postgres test.yml`
- [ ] Scan a database with `fides scan dataset db --credentials-id app_postgres`

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

- [ ] Verify the ethyca-fides release is published to PyPi: <https://pypi.org/project/ethyca-fides/#history>
- [ ] Verify the fides release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides>
- [ ] Verify the fides-privacy-center release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides-privacy-center>
- [ ] Verify the fides-sample-app release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides-sample-app>
- [ ] Smoke test the PyPi & DockerHub releases with a clean `pip install ethyca-fides` and `fides deploy up`
