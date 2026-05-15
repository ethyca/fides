## Summary

<!-- What's being changed. One sentence is usually enough. -->

## Type

<!-- Check one or more — helps reviewers know what to look at. -->

- [ ] Dependency bump
- [ ] Build / CI configuration
- [ ] Tooling (linter, formatter, scripts)
- [ ] Repo housekeeping (configs, ignore files, docs)
- [ ] Other:

## Linked issues

<!-- Optional. "Refs #123" or a Dependabot/Renovate link if applicable. -->

## Why

<!-- Brief. "Security advisory GHSA-xxxx", "unblocks Node 22 upgrade", "matches new team convention", etc. -->

## For dependency bumps

<!-- Delete this whole section if not a dependency change. -->

- **Package:** 
- **From → To:** 
- **Changelog / release notes:** <!-- link -->
- [ ] Reviewed breaking changes
- [ ] No breaking changes affect us, or — required migrations are included in this PR

## Testing

- [ ] CI passes
- [ ] Locally verified the relevant workflow still works <!-- e.g., "build still succeeds", "linter still runs", "tests still pick up" -->

## Risk

<!-- Most chores are low-risk. If this one isn't (e.g., touching CI that gates deploys, bumping a load-bearing dep), say so. Otherwise: "Low — config/tooling only." -->

## Pre-merge checklist

- [ ] All CI pipelines succeeded
- [ ] Changelog entry added under `changelog/` (`{pr-number}-{slug}.yaml`)
  - [ ] `high-risk` label added if this could cause performance impact or unexpected regression
  - [ ] `db-migration` label added if this PR includes a DB migration
- [ ] Database migrations
  - [ ] Downrev is up to date with the latest revision on the base branch
  - [ ] `downgrade()` migration is correct and tested
  - [ ] _Or:_ a downgrade is not possible — called out explicitly in the PR description
  - [ ] _Or:_ no migrations in this PR
