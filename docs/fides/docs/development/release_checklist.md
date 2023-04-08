# Release Checklist

The release checklist is a manual set of checks done before each release to ensure functionality of the most critical components of the application. Some of these steps are redundant with automated tests, while others are _only_ tested here as part of this check.

This checklist should be copy/pasted into the final pre-release PR, and checked off as you complete each step.

## Pre-Release Steps

### General

From the release branch, confirm the following:
- [ ] Quickstart works: `nox -s quickstart` (verify you can complete the interactive prompts from the command-line)
- [ ] Test environment works: `nox -s "fides_env(test)"` (verify the admin UI on localhost:8080, privacy center on localhost:3001, CLI and webserver)
- [ ] Building the sample app images works: `nox -s "build(sample)"` (creates the sample images, which is also prereq for `fides deploy up --no-pull` next)
- [ ] Running the CLI deploy works: `fides deploy up --no-pull` (see instructions below...)

```
mkdir ~/fides-deploy-test
cd ~/fides-deploy-test
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/ethyca/fides.git@<release-branch-name-here>
fides deploy up --no-pull
fides status
fides deploy down
rm -rf ~/fides-deploy-test
exit
```

Next, run the following checks using the test environment (`nox -s "fides_env(test)"`):

### API

- [ ] Verify that the generated API docs are correct (http://localhost:8080/docs)

### CLI

Run these from within the test environment shell:

- [ ] Make sure to login your CLI user by running `fides user login -u root_user -p Testpassword1!`
- [ ] Run a `fides push`
- [ ] Run a `fides pull`
- [ ] Run a `fides evaluate`
- [ ] Generate a dataset with `fides generate dataset db --credentials-id app_postgres test.yml`
- [ ] Scan a database with `fides scan dataset db --credentials-id app_postgres`

### Privacy Center

- [ ] Every navigation button works
- [ ] DSR submission succeeds
- [ ] Consent request submission succeeds

### Admin UI

- [ ] Every navigation button works
- [ ] DSR approval succeeds
- [ ] DSR execution succeeds

### Documentation

- [ ] Verify that the CHANGELOG is formatted correctly and clean up verbiage where needed
- [ ] Verify that the CHANGELOG is representative of the actual changes

## Post-Release Steps

- [ ] Verify the ethyca-fides release is published to PyPi: <https://pypi.org/project/ethyca-fides/#history>
- [ ] Verify the fides release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides>
- [ ] Verify the fides-privacy-center release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides-privacy-center>
- [ ] Verify the fides-sample-app release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides-sample-app>
- [ ] Smoke test the PyPi & DockerHub releases with a clean `pip install ethyca-fides` and `fides deploy up`
- [ ] Announce the release!
