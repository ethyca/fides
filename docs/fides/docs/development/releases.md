# Releases

## Versioning

Fides uses semantic versioning. Due to the rapid development of the project, some minor versions may also contain minor breaking changes. The best practice is to always pin versions, and carefully test before bumping to a new version. 

Patch versions will never cause breaking changes, and are only used to hotfix critical bugs.

## Release schedule

Fides does not follow a set release schedule, and instead ships versions based on the addition of features and functionality. Each release, with the exception of hotfixes, will contain at least one substantial new feature.

## Planning

For each release, a corresponding [GitHub Project](https://github.com/ethyca/fides/projects) is created. Issues are added to projects as a way to organize what will be included in each release.

Once a release project is complete and the core team signs off on the readiness of the release, a new version is cut using GitHub releases. You can see all Fides releases [here](https://github.com/ethyca/fides/releases). Each new release triggers a GitHub Action that pushes the new version to PyPI, and a clean version to DockerHub. The release project is then marked as `closed`.

Hotfixes are an exception to this, and can be added and pushed as patch versions when needed.

## Branching

Fides uses continuous delivery with a single `main` branch. All code changes are merged into this branch. 

When releasing, a new tag is created, and the release process proceeds automatically. 

In the case of patches, a branch is created from the relevant tag. Commits are then cherry-picked into this branch, and a new patch version tag is created.

## Release Steps

We use GitHub’s `release` feature to tag releases that then get automatically deployed to DockerHub and PyPi via GitHub Actions pipelines. We also use a `CHANGELOG.md` to make sure that our users are never surprised about an upcoming change and can plan upgrades accordingly. The release steps are as follows:

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
