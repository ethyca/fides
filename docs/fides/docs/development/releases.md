# Releases

---

## Versioning

Fidesctl uses semantic versioning. Due to the rapid development of the project, some minor versions may also contain minor breaking changes. Best practice is always pinning versions and carefully testing before bumping to a new version. Patch versions will never cause breaking changes, and are only used to hotfix critical bugs.

## Release Schedule

Fidesctl does not follow a set release schedule, but instead ships versions based on the addition of features/functionality. Each release, with the exception of hotfixes, will contain at least one substantial new feature.

## Planning

For each release a corresponding GitHub Project is created. These projects can be found [here](https://github.com/ethyca/fides/projects). Issues are then added to release projects as a way to organize what will be included in each release.

Once a release project is complete and the core team signs off on the readiness of the release, a new version is cut using GitHub releases. You can see all fidesctl releases [here](https://github.com/ethyca/fides/releases). Each new release triggers a GitHub Action that pushes the new version to PyPI as well as pushes a clean version to DockerHub. The release project is then marked as `closed`.

Hotfixes are an exception to this and can be added and pushed as patch versions when needed.

## Branching

Fidesctl uses continuous delivery with a single `main` branch. All code changes get merged into this branch. For releases, a new tag is created and the release process kicks off automatically. In the case of patches, a branch is created from the relevant tag and commits are then cherry-picked into it and a new patch version tag is created.

## Release Steps

We use GitHub’s `release` feature to tag releases that then get automatically deployed to DockerHub & PyPi via GitHub Actions pipelines. We also use a `CHANGELOG.md` to make sure that our users are never surprised about an upcoming change and can plan upgrades accordingly. The release steps are as follows:

### Major
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

### Minor
1. Create a new branch from the latest tagged release being patched (i.e. `1.6.0`)
1. Use `git cherry-pick <commit>` to incorporate specific changes required for the minor release
1. Copy the `Unreleased` section of `CHANGELOG.md` and paste above the release being patched
    * Rename `Unreleased` to the new version number and put a date next to it
    * Cut and paste the changes documented that are now included in the minor release in the correct section
1. Open a PR that is titled the version of the release (i.e. `1.6.1`), add the `do not merge` label
1. Due to potential merge conflicts when opening against main, checks may need to be run manually
1. Create a new release, using the branch created in step 1
1. Add the new version as the tag (i.e. `1.6.1`)
1. Make the title the version with a `v` in front of it (i.e. `v1.6.1`)
1. Add a link to the `CHANGELOG.md` (the changes are not merged yet but can be planned for)
1. Auto-populate the release notes
1. Publish the release
1. Create a new branch from `main`
1. Copy the changes from `CHANGELOG.md` for the minor release into the new branch
1. Open a separate PR for the `CHANGELOG.md` updates for the minor release, once approved merge the PR
1. Close the original PR made for the release (labeled `do not merge`) without merging
