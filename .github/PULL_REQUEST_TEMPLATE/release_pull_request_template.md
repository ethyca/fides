## Release Checklist

The release checklist is a manual set of checks done before each release to ensure functionality of the most critical components of the application. Some of these steps are redundant with automated tests, while others are _only_ tested here as part of this check.

This checklist should be copy/pasted into the final pre-release PR, and checked off as you complete each step.

Additionally, there is a robust [Release Process](https://ethyca.atlassian.net/wiki/spaces/EN/pages/2545483802/Release+Process+Fides) page available in Confluence (_internal only_).


> [!WARNING]
> THIS RELEASE BRANCH PULL REQUEST SHOULD NOT BE MERGED! IT IS FOR TRACEABILITY PURPOSES ONLY!

### Pre-Release Steps

#### General

From the release branch, confirm the following:

* [ ] Quickstart works: `nox -s quickstart` (verify you can complete the interactive prompts from the command-line)
* [ ] Test environment works: `nox -s "fides_env(test)"` (verify the admin UI on localhost:8080, privacy center on localhost:3001, CLI and webserver)
* [ ] Have Roger run a QATouch automation run

Next, run the following checks via the test environment:

#### API

* [ ] Verify that the generated API docs are correct @ <http://localhost:8080/docs>

#### CLI

Run these from within the test environment shell:

* [ ] `git reset --hard` - **Note: This is required for the `pull` command to work**
* [ ] `fides user login`
* [ ] `fides push src/fides/data/sample_project/sample_resources/`
* [ ] `fides pull src/fides/data/sample_project/sample_resources/`
* [ ] `fides evaluate src/fides/data/sample_project/sample_resources/`
* [ ] `fides generate dataset db --credentials-id app_postgres test.yml` - **Note: Because the filesystem isn't mounted, the new file will only show up within the container**
* [ ] `fides scan dataset db --credentials-id app_postgres`

#### Privacy Center

* [ ] Every navigation button works
* [ ] DSR submission succeeds
* [ ] Consent request submission succeeds

#### Admin UI

* [ ] Every navigation button works
* [ ] DSR approval succeeds
* [ ] DSR execution succeeds

### User Permissions

- [ ] Verify user creation
- [ ] Verify a Viewer can view all systems
- [ ] Verify a Data Steward can edit systems they are assigned

#### Documentation

* [ ] Verify that the CHANGELOG is formatted correctly and clean up verbiage where needed
* [ ] Verify that the CHANGELOG is representative of the actual changes

:warning: Note that any updates that need to be made to the CHANGELOG should **not** be commited directly to the release branch.
Instead, they should be committed on a branch off of `main` and then PR'd and merged into `main`, before being cherry-picked
over to the release branch. This ensures that the CHANGELOG stays consistent between the release branch and `main`.

#### Publishing the release

When publishing the release, be sure to include the following sections in the release description:

* [ ] `## Release Pull Request` section that includes a link back to the release PR (i.e., this one!) for tracking purposes
* [ ] `## QA Touch Test Run` section that includes a link to the QATouch test run (QA team should provide this)

### Post-Release Steps

* [ ] Verify the ethyca-fides release is published to PyPi: <https://pypi.org/project/ethyca-fides/#history>
* [ ] Verify the fides release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides>
* [ ] Verify the fides-privacy-center release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides-privacy-center>
* [ ] Verify the fides-sample-app release is published to DockerHub: <https://hub.docker.com/r/ethyca/fides-sample-app>
* [ ] Smoke test the PyPi & DockerHub releases:
    * [ ] Create a fresh venv with `python3 -m venv 2_12_0_venv`
    * [ ] Activate the venv `source 2_12_0_venv/bin/activate`
    * [ ] `pip install ethyca-fides`
    * [ ] `fides deploy up`
* [ ] Announce the release!
