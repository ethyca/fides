## Summary

<!-- What capability does this add, and who is it for? One or two sentences. -->

## Linked issues

<!-- Use "Closes [ENG-1234]" for the spec/ticket, "Refs [ENG-1234]" for related discussion.
     Brackets around the ticket ID let the Atlassian GitHub integration auto-link it. -->
Closes [ENG-]

## What's new

<!-- The user-visible (or API-visible) behavior. Describe it as if writing release notes. -->

## What's explicitly out of scope

<!-- Things a reviewer might expect to see but that are intentionally not in this PR. Prevents scope-creep review feedback. -->

## Screenshots / recording

<!-- Required for any UI change. For API changes, include a sample request/response. Delete only if there is truly no observable surface. -->

## How to test this

<!-- Instructions for the reviewer. Delete this section only if there is genuinely nothing to verify by hand. -->

**Setup:** <!-- branch checked out, env vars, seed data, feature flag to enable, etc. Skip the line if no setup beyond the usual. -->

1. 
2. 
3. 

**Expected:** <!-- the new behavior the reviewer should observe -->

**Also worth trying:** <!-- optional — edge cases, failure modes, or adjacent flows worth a quick poke -->

## Design / approach

<!-- Brief note on the implementation approach. Skip if the diff is self-explanatory. Call out anything non-obvious: new abstractions, why you chose X over Y, anything reviewers shouldn't have to reverse-engineer. -->

## Testing

- [ ] Unit tests for new logic
- [ ] Integration / end-to-end coverage where it matters
- [ ] Manually tested the happy path
- [ ] Manually tested at least one failure / edge case

**What I tested manually:**

<!-- Bullet the scenarios. Be specific. -->

## Rollout

- [ ] Behind a feature flag — flag name: 
- [ ] Safe to ship to everyone immediately
- [ ] Requires a migration / backfill (describe below)
- [ ] Requires coordination with another team / service (describe below)

<!-- Add detail for any checked box that needs it. -->

## Risk & rollback

<!-- What breaks if this is wrong? How do we turn it off? If it's flag-gated, say so. If revert is the answer, say so. -->

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
