# RFC: Adopt Git Flow Branching Model and Automate Release Process

**Author:** Adrian Galvan
**Status:** Request for Comment
**Date:** 2026-04-01

## Summary

This RFC proposes replacing our current release branching strategy with **Git Flow** (main/dev/release branches) and automating the mechanical steps of the release process. The primary goal is to eliminate cherry-picking from the release workflow entirely, removing the class of errors it introduces: missing related changes, migration conflicts, and Alembic multiple-head failures.

## Motivation

Our current release process (documented in [WIP: Release Process 2025](https://ethyca.atlassian.net/wiki/spaces/EN/pages/2545483802) and [Patch Release Process 2025](https://ethyca.atlassian.net/wiki/spaces/EN/pages/3807313921)) relies on cherry-picking commits from `main` to the release branch. This creates several recurring problems:

1. **Cherry-picks miss related changes.** A squash-merged PR on `main` may depend on other recent commits. Cherry-picking a single commit brings the fix but not its dependencies, causing build or test failures on the release branch.

2. **Migration conflicts.** Migrations merged to `main` after the release branch is cut change the Alembic revision graph. Cherry-picking a commit that includes or depends on a migration can fail outright or produce Alembic "multiple heads" errors on the release branch.

3. **Manual, error-prone process.** The release manager must identify the correct squash commit hashes, cherry-pick them in order, resolve conflicts, update `requirements.txt` manually, and push new RC tags after each fix. Each step is a place where things can go wrong.

4. **Patch releases amplify the pain.** Patch releases branch off previous release branches and cherry-pick from `main`, compounding the divergence. The patch release doc itself notes that running a patch "off of main" avoids cherry-picking entirely, acknowledging the problem implicitly.

## Proposal

### Branching Model: Git Flow

Adopt three long-lived branches:

| Branch | Purpose | Who merges here |
|--------|---------|-----------------|
| `main` | Always reflects the latest **released** code. Tagged with release versions. | Release manager (merge from release branch) |
| `dev` | Integration branch for all feature work. This is where PRs land day-to-day. | Engineers (via PR) |
| `release/2.x.0` | Stabilization branch cut from `dev` when preparing a release. Short-lived (one release cycle). | Release manager + engineers fixing release bugs |

```
main ──────────────────────────────────● tag 2.x.0
                                      /
release/2.x.0 ──●──fix──fix────────●
               /                     \
dev ──●──●──●─/ ──●──●──●────────────● merge back from release
       features     features continue
```

### How It Works

#### Day-to-day development
- All feature branches are created from and merged into `dev`.
- `main` is not a merge target during normal development.

#### Release creation (Wednesday)
1. Cut `release/2.x.0` from `dev`.
2. Generate changelog, create draft PR (for traceability, not to merge), push RC tag.
3. `dev` remains open for feature work. Engineers are **not blocked**.

#### Bug fixes during stabilization (Thursday)
- Fixes are authored on branches created from `release/2.x.0` and merged directly into the release branch via PR.
- After merging to the release branch, the fix is **merged** (not cherry-picked) back into `dev`. This can be automated as a PR created on each merge to the release branch.
- New RC tags are pushed after each fix.

#### Publishing the release (Monday)
1. Tag `release/2.x.0` for the final release.
2. Merge `release/2.x.0` into `main`. If Alembic multiple heads exist (from migrations that landed on `dev` and were merged to `main` via a previous release), resolve with `alembic merge heads` as part of this merge.
3. Merge `release/2.x.0` back into `dev` (if not already fully merged via individual fix merges).
4. Delete the release branch.

#### Patch releases
- Cut `release/2.x.1` from the **tag** on `main` (e.g., `2.x.0`).
- Apply fixes directly to the patch release branch.
- Merge back to `dev` (and `main` when releasing).
- No cherry-picking required.

#### Hotfixes
- For critical production issues between releases: branch from `main`, fix, merge to both `main` (with tag) and `dev`.

### What Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| Default PR target | `main` | `dev` |
| Release branch cut from | `main` | `dev` |
| Release bug fixes | Merge to `main`, cherry-pick to release | Merge directly to release branch, then merge to `dev` |
| Alembic conflicts from cherry-pick | Common | Eliminated |
| Alembic heads on main | N/A (release branch not merged to main) | Resolved with `alembic merge heads` on release-to-main merge |
| Patch releases | Cherry-pick from `main` to new release branch | Branch from tag on `main`, fix directly |
| Release branch merged to main? | Never (traceability PR only) | Yes, this is how released code reaches `main` |

### Alembic "Multiple Heads" Strategy

The one place where multiple heads can still arise is when merging a release branch into `main`, if `main` has received a hotfix with its own migration since the last release. This is a mechanical, well-understood resolution:

```bash
# After merging release into main, if heads diverged:
alembic merge heads -m "merge migration heads for 2.x.0 release"
```

This can be detected and resolved automatically as part of the release merge PR. A CI check or pre-merge script can run `alembic heads` and, if multiple heads exist, generate the merge migration and include it in the PR.

### Fidesplus Coordination

The two-repo coordination largely stays the same, with the same improvement applied:

1. Fidesplus also adopts `dev`/`main`/`release` branches.
2. Fides RC is published to PyPI from its release branch (same as today).
3. Fidesplus release branch updates `requirements.txt` to point to the Fides RC (same as today).
4. Bug fixes during release go directly on the fidesplus release branch (no cherry-pick).

## What Can Be Automated

Nearly every mechanical step in the current process is scriptable. Automation targets, roughly ordered by impact:

### High impact
| Step | How |
|------|-----|
| Cut release branch + create draft PR | Single `gh` CLI / GitHub Action triggered by schedule or command |
| Changelog generation | Already scripted (`nox -s changelog`); can be triggered automatically on branch cut |
| Push RC tags after merge to release branch | GitHub Action on merge event to `release/*` |
| Merge release fixes back to `dev` | GitHub Action creates a PR automatically on each merge to `release/*` |
| Update fidesplus `requirements.txt` | Script watches for fides RC on PyPI, updates and pushes |
| Alembic head merge on release-to-main | CI check detects multiple heads and generates merge migration |

### Medium impact
| Step | How |
|------|-----|
| Slack announcements | Slack webhook triggered by GitHub Actions at each stage |
| RC environment deployment verification | Health check script that polls the About page for expected version |
| Beta tag bump on main after release | GitHub Action triggered after release tag is published |

### Lower priority (human judgment still valuable)
| Step | How |
|------|-----|
| Release readiness decision | Checklist automation can verify all items, but go/no-go is a human call |
| Release notes curation | Auto-generated from changelog, but may need editing |
| Bug triage during stabilization | Requires product + engineering judgment |

## Migration Plan

Switching to Git Flow requires a one-time cutover. Proposed approach:

1. **After the next release ships:** rename `main` to `dev` in both repos (or create `dev` from `main`), then create a new `main` that points to the release tag.
2. **Update branch protection rules** on GitHub for `dev` and `main`.
3. **Update CI/CD workflows** to trigger on `dev` (for feature PRs) and `release/*` (for RC builds).
4. **Update contributor docs** and PR templates to target `dev`.
5. **First release under new model** runs in parallel with the old process as a dry run.

## Open Questions

1. **Naming: `dev` vs `develop`?** Git Flow traditionally uses `develop`, but `dev` is shorter and what we already use in conversation. Preference?

2. **Merge strategy for release-to-main:** Regular merge commit (preserves full history) or squash merge (cleaner main history)? Merge commit is more standard for Git Flow and avoids losing the individual fix commits.

3. **Automation scope for v1:** Should we automate everything listed above from day one, or adopt the branching model first and layer in automation incrementally?

4. **Release branch naming:** Keep `release-2.x.0` (current convention) or switch to `release/2.x.0` (Git Flow convention, works with glob patterns in CI)?

5. **Who can merge to `main`?** With `main` as the released-code branch, should we restrict merge permissions to release managers only?

6. **How does this affect the fidesplus-poc workflow?** The silicon image build and fidesplus-poc.sh update process needs to be mapped to the new branching model.

## References

- [Current Release Process (2025)](https://ethyca.atlassian.net/wiki/spaces/EN/pages/2545483802)
- [Current Patch Release Process (2025)](https://ethyca.atlassian.net/wiki/spaces/EN/pages/3807313921)
- [A Successful Git Branching Model (Vincent Driessen, 2010)](https://nvie.com/posts/a-successful-git-branching-model/)
- [Release PR Template](https://github.com/ethyca/fides/blob/main/.github/PULL_REQUEST_TEMPLATE/release_pull_request_template.md)
