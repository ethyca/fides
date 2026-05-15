## Summary

<!-- One sentence: what's being reverted and why. -->

This reverts #<!-- PR number --> ("<!-- title of the reverted PR -->").

## Why we're reverting

<!-- What went wrong. Be specific: error rate spike, customer report, broken build, regression caught in QA, etc. Link to the alert / incident / report if there is one. -->

## Impact of the original change

<!-- What did the reverted PR break, and for whom? If there was user-visible impact (errors served, bad data written, etc.), call that out — it may need separate cleanup. -->

## Cleanup beyond the revert

<!-- Anything the revert alone doesn't fix? -->

- [ ] No further cleanup needed — revert is sufficient
- [ ] Data needs to be cleaned up / backfilled (describe below)
- [ ] Feature flag needs to be turned off / removed (describe below)
- [ ] Downstream notifications sent (describe below)

<!-- Detail for any checked box. -->

## What happens to the original work

<!-- Reverting isn't abandoning. State the plan: -->

- [ ] Will be re-attempted in a follow-up PR — tracking issue: #
- [ ] Abandoned — reason: 
- [ ] Other:

## How to test this

<!-- How the reviewer can confirm the original problem is actually resolved by this revert. Delete if not applicable (e.g. revert of an unmerged-to-prod change with no observable trace). -->

**Setup:** <!-- skip if none -->

1. 
2. 

**Expected:** <!-- the broken behavior introduced by the reverted PR should no longer occur -->

## Testing

- [ ] CI passes on the revert
- [ ] Verified the original problem is gone

## Risk

<!-- Reverts are usually safe but not always — especially if anything has been built on top of the reverted PR since it merged. Note any such follow-on changes. -->

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
- [ ] UX review
  - [ ] Reviewed by a designer
  - [ ] _Or:_ no UX changes
- [ ] Documentation
  - [ ] PR opened in [fidesdocs](https://github.com/ethyca/fidesdocs/pulls)
  - [ ] _Or:_ issue created in [fidesdocs](https://github.com/ethyca/fidesdocs/issues/new/choose)
  - [ ] _Or:_ new client scopes — public-facing scope registry docs updated
  - [ ] _Or:_ no documentation updates required
- [ ] Verified on demo environment (`nox -s dev -- demo`)
