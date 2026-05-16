## Summary

<!-- One or two sentences: what was broken and what this PR does about it. -->

## Linked issues

<!-- Use "Fixes [ENG-1234]" for the ticket this PR resolves, "Refs [ENG-1234]" for related context.
     Brackets around the ticket ID let the Atlassian GitHub integration auto-link it. -->
Fixes [ENG-]

## Root cause

<!-- The actual underlying cause — not just the symptom. If the cause is a class of mistake we've made before, say so. -->

## The fix

<!-- What this PR changes, and why this approach over alternatives you considered. -->

## Reproduction

<!-- Steps to reproduce the bug before this PR. Keep it terse. If there's a failing test that demonstrates it, point to that instead. -->

1. 
2. 
3. 

**Expected:** 
**Actual (before this PR):** 

## Screenshots / recording

<!-- Before/after if user-visible. Delete this section if not applicable. -->

## How to test this

<!-- Instructions for the reviewer. Delete this section only if there is genuinely nothing to verify by hand (e.g. internal-only change covered fully by an automated regression test). -->

**Setup:** <!-- branch checked out, env vars, seed data, feature flag, etc. Skip the line if no setup beyond the usual. -->

1. 
2. 
3. 

**Expected:** <!-- what should happen now that didn't before -->

**Also worth trying:** <!-- optional — edge cases or adjacent flows the reviewer might want to poke at -->

## Testing

- [ ] Added a regression test that fails without this fix
- [ ] Existing tests pass locally
- [ ] Manually verified the reproduction no longer reproduces

<!-- If a regression test isn't feasible, explain why. "Hard to test" is not a sufficient reason — "requires production data we don't have in CI" is. -->

## Risk

<!-- Who/what could this affect beyond the bug itself? Any code paths that share the changed logic? -->

**Rollback plan:** <!-- Usually "revert this PR." Say so if it's anything more complicated. -->

## Pre-merge checklist

- [ ] All CI pipelines succeeded
- [ ] Issue requirements met
- [ ] Changelog entry added under `changelog/` (`{pr-number}-{slug}.yaml`)
  - [ ] `high-risk` label added if this could cause performance impact or unexpected regression
  - [ ] `db-migration` label added if this PR includes a DB migration
- [ ] Database migrations
  - [ ] Downrev is up to date with the latest revision on the base branch
  - [ ] `downgrade()` migration is correct and tested
  - [ ] _Or:_ a downgrade is not possible — called out explicitly in the PR description
  - [ ] _Or:_ no migrations in this PR
- [ ] UX review
  - [ ] Reviewed by a designer
  - [ ] _Or:_ no UX changes
- [ ] Documentation
  - [ ] PR opened in [fidesdocs](https://github.com/ethyca/fidesdocs/pulls)
  - [ ] _Or:_ issue created in [fidesdocs](https://github.com/ethyca/fidesdocs/issues/new/choose)
  - [ ] _Or:_ new client scopes — public-facing scope registry docs updated
  - [ ] _Or:_ no documentation updates required
- [ ] Verified on demo environment (`nox -s dev -- demo`)
