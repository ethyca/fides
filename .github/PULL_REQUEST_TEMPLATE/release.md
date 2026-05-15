> [!WARNING]
> **THIS RELEASE BRANCH PR SHOULD NOT BE MERGED.** It exists for traceability and to track the release checklist. Close it (don't merge it) once the release is complete.

# Release checklist

Copy the state of this checklist into the release notes / release ticket as you go. Check items off as completed.

## Pre-release

### General

From the release branch, confirm the following:

- [ ] Quickstart works: `nox -s quickstart` (verify you can complete the interactive prompts from the command-line)
- [ ] Test environment works: `nox -s "fides_env(test)"` (verify the admin UI on localhost:8080, privacy center on localhost:3001, CLI and webserver)

Next, run the following checks via the test environment:

### API

- [ ] Generated API docs are correct at <http://localhost:8080/docs>

### CLI

Run these from within the test environment shell:

- [ ] `git reset --hard` — **required for the `pull` command to work**
- [ ] `fides user login`
- [ ] `fides push src/fides/data/sample_project/sample_resources/`
- [ ] `fides pull src/fides/data/sample_project/sample_resources/`
- [ ] `fides evaluate src/fides/data/sample_project/sample_resources/`
- [ ] `fides generate dataset db --credentials-id app_postgres test.yml` — **the filesystem isn't mounted, so the new file will only show up inside the container**
- [ ] `fides scan dataset db --credentials-id app_postgres`

### Privacy Center

- [ ] Every navigation button works
- [ ] DSR submission succeeds
- [ ] Consent request submission succeeds

### Admin UI

- [ ] Every navigation button works
- [ ] Login/logout succeeds
- [ ] DSR approval succeeds
- [ ] DSR execution succeeds

### Documentation

- [ ] CHANGELOG is formatted correctly and accurately represents the actual changes in this release

> [!IMPORTANT]
> **CHANGELOG fixes do not go on the release branch.** Commit them on a branch off `main`, PR and merge to `main`, then cherry-pick to the release branch. This keeps the CHANGELOG consistent between `main` and the release branch.

### Publishing the release

- [ ] Release description includes a `## Release Pull Request` section linking back to **this** PR for traceability

## Post-release

- [ ] `ethyca-fides` release published to PyPI: <https://pypi.org/project/ethyca-fides/#history>
- [ ] `fides` release published to DockerHub: <https://hub.docker.com/r/ethyca/fides>
- [ ] `fides-privacy-center` release published to DockerHub: <https://hub.docker.com/r/ethyca/fides-privacy-center>
- [ ] `fides-sample-app` release published to DockerHub: <https://hub.docker.com/r/ethyca/fides-sample-app>

## Sign-off

- [ ] All applicable checklist items above are complete (or explicitly marked N/A with reason)
- [ ] Release published and verified
- [ ] This PR is being closed (not merged)
