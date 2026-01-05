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

## Changelog Entries

To avoid merge conflicts in `CHANGELOG.md`, we use a fragment-based system where each PR adds a YAML file describing the change.

### Creating a Changelog Entry

When creating a PR, add a changelog entry file:

1. Copy `changelog/TEMPLATE.yaml` to a new file in the `changelog/` directory
2. Name the file using your PR number (e.g., `7137.yaml`) or a descriptive slug (e.g., `add-gpc-fields.yaml`)
3. Fill in the required fields:
   - `type`: One of: Added, Changed, Developer Experience, Deprecated, Docs, Fixed, Removed, Security
   - `description`: Short description of the change (without the leading `-`)
   - `pr`: PR number (optional if not yet known)
   - `labels`: Optional list of labels: `high-risk`, `db-migration`

Example (`changelog/7137.yaml`):

```yaml
type: Added
description: Added editable GPC translation fields to privacy experience configuration
pr: 7137
labels: []
```

The changelog entry will be automatically compiled into `CHANGELOG.md` during the release process.

## Release Steps

We use GitHub's `release` feature to tag releases that then get automatically deployed to DockerHub and PyPi via GitHub Actions. We also use a `CHANGELOG.md` to mitigate surprises to our users and help them plan updates accordingly. The release steps are as follows:

### Major and Minor

1. Compile changelog fragments into `CHANGELOG.md`:
   ```sh
   # Preview what will be generated (dry run)
   nox -s "changelog(dry)"

   # Compile fragments and finalize for release
   nox -s "changelog(write)" -- --release 2.76.0
   ```
   This will:
   - Compile all YAML fragments from `changelog/` into the Unreleased section
   - Create a new version section with all Unreleased content
   - Leave the `Unreleased` section empty at the top (ready for new entries)
   - Update the `compare` links for both the new version and the `Unreleased` section
   - Delete the processed fragment files

1. Open a PR that is titled the version of the release (i.e. `2.76.0`) with the updated `CHANGELOG.md`
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

1. Compile changelog fragments for the patch release:
   ```sh
   # Preview what will be generated (dry run)
   nox -s changelog(dry) -- --prs 1234,5678

   # Compile fragments and finalize for patch release (only selected PRs)
   nox -s "changelog(write)" -- --release 1.2.4 --prs 1234,5678
   ```
   This will:
   - Compile only the YAML fragments matching the specified PR numbers (comma-separated list)
   - Create a new version section from those entries
   - Leave the `Unreleased` section empty at the top
   - Delete only the processed fragment files (matching PRs)
   - Leave other fragment files in `changelog/` for future releases
   - Update compare links appropriately

   **Note:** For patch releases, you typically only want to include specific PRs. Use the `--prs` flag to specify which PR numbers to include. Fragments without PR numbers will be skipped when using this flag.
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

Please use the [checklist defined in `.github/PULL_REQUEST_TEMPLATE/release_pull_request.md`](https://github.com/ethyca/fides/blob/HEAD/.github/PULL_REQUEST_TEMPLATE/release_pull_request_template.md) as a release checklist. This should be put in the description for PRs of release branches.
