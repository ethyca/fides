# Releases

## Versioning

Fides uses semantic versioning. Due to the rapid development of the project, some minor versions may also contain minor breaking changes. The best practice is to always pin versions, and carefully test before bumping to a new version.

Patch versions will never cause breaking changes, and are only used to hotfix critical bugs.

## Release schedule

Fides does not follow a set release schedule, and instead ships versions based on the addition of features and functionality. Each release, with the exception of hotfixes, contains at least one substantial new feature.

## Branching

Fides uses continuous delivery with a single `main` branch. All code changes are merged into this branch.

When it comes times to prepare for a new release, a release branch is created for stability and thoroughly tested.

When releasing, a new tag is created on the release branch and the release process proceeds automatically.

In the case of patches, a branch is created from the relevant tag. Commits are then cherry-picked into this branch, and a new patch version tag is created.

## Release Steps

We use GitHub’s `release` feature to tag releases that then get automatically deployed to DockerHub and PyPi via GitHub Actions. We also use a `CHANGELOG.md` to mitigate surprises to our users and help them plan updates accordingly. The release steps are as follows:

### Major and Minor

1. Open a PR that is titled the version of the release (i.e. `1.6.0`)
    * Rename the `Unreleased` section of `CHANGELOG.md` to the new version number and put a date next to it
    * Update the `compare` links for both the new version and for the new `Unreleased` section
1. Once approved, merge the PR
1. Create a new release, ensuring that the last PR to get merged is the aforementioned `CHANGELOG.md` update PR
1. Add the new version as the tag (i.e. `1.6.0`)
1. Make the title the version with a `v` in front of it (i.e. `v1.6.0`)
1. Add a link to the `CHANGELOG.md`
1. Auto-populate the release notes
1. Publish the release

### Patch

It may be necessary for a patch release to contain only select commits to the `main` branch since the last major or minor release. To create a release with only the desired changes, follow the steps below:

1. Checkout the most recent release's tag
    1. To fetch the most recent tag's name, run:

        ```sh
        # fides on main
        git describe --abbrev=0 --tags

        #=> 1.2.3
        ```

    1. To checkout the most recent tag, run:

        ```sh
        #fides on main
        git checkout 1.2.3

        #=> Note: switching to '1.2.3'.
        #
        # You are in 'detached HEAD' state. You can look around, make experimental
        # changes and commit them, and you can discard any commits you make in this
        # state without impacting any branches by switching back to a branch.
        #
        # If you want to create a new branch to retain commits you create, you may
        # do so (now or later) by using -c with the switch command. Example:
        #
        # git switch -c <new-branch-name>
        #
        # Or undo this operation with:
        #
        # git switch -
        #
        # Turn off this advice by setting config variable advice.detachedHead to false
        #
        # HEAD is now at 0123abcd Commit Message
        ```

    !!! tip
        This can be combined into a single command:

        ```sh
        # fides on main
        git checkout $(git describe --abbrev=0 --tags)

        #=> Note: switching to '1.2.3'.
        #
        # You are in 'detached HEAD' state. You can look around, make experimental
        # changes and commit them, and you can discard any commits you make in this
        # state without impacting any branches by switching back to a branch.
        #
        # If you want to create a new branch to retain commits you create, you may
        # do so (now or later) by using -c with the switch command. Example:
        #
        # git switch -c <new-branch-name>
        #
        # Or undo this operation with:
        #
        # git switch -
        #
        # Turn off this advice by setting config variable advice.detachedHead to false
        #
        # HEAD is now at 0123abcd Commit Message
        ```

1. Create a new branch from the `HEAD` commit of the most recent release's tag, called `release-v<tag>`

    ```sh
    # fides on tags/1.2.3
    git checkout -b release-v1.2.4

    #=> Switched to a new branch 'release-v1.2.4'
    ```

1. If the changes to be included in the patch release are contained in one or more unmerged pull requests, change the base branch of the pull request(s) to the release branch created in the previous step
1. Once approved, merge the pull request(s) into the release branch
1. Create a new branch off of the release branch by running:

    ```sh
    # fides on release-v1.2.4
    git checkout -b prepare-release-v1.2.4

    #=> Switched to a new branch 'prepare-release-v1.2.4'
    ```

1. **Optional:** Incorporate any additional specific changes required for the patch release by running:

    ```sh
    # fides on prepare-release-v1.2.4
    git cherry-pick <commit>...
    ```

1. Copy the `Unreleased` section of `CHANGELOG.md` and paste above the release being patched
    1. Rename `Unreleased` to the new version number and put a date next to it
    1. Cut and paste the documented changes that are now included in the patch release to the correct section
    1. Commit these changes
1. Open a pull request to incorporate any cherry-picked commits and the `CHANGELOG.md` changes into the release branch
    1. Set the base branch of this pull request to the release branch
    1. Once approved, merge the pull request into the release branch
1. Create a new release from the release branch
    1. Add the new version as the tag (i.e. `1.2.4`)
    1. Title the release with the version number, prefixed with a `v` (i.e. `v1.2.4`)
    1. Add a link to the `CHANGELOG.md`
    1. Auto-populate the release notes
1. Publish the release
1. Merge the new release tag into `main`

    !!! warning
        Pushing commits (including merge commits) to the `main` branch requires admin-level repository permissions.

    1. Checkout the `main` branch, and update the local repository:

        ```sh
        git checkout main
        #=> Switched to branch 'main'...

        git pull
        ```

    1. Merge the new release tag into `main`:

        ```sh
        git merge tags/1.2.4
        ```

    1. Handle any merge conflicts, and push to the remote `main` branch

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
