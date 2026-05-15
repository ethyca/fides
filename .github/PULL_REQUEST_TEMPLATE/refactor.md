## Summary

<!-- What you're restructuring and why. One or two sentences. -->

## Motivation

<!-- Why this is worth doing now. Reducing duplication, unblocking upcoming work, paying down a specific piece of tech debt, etc. "It felt messy" is not enough on its own — say what it costs us. -->

## Linked issues

<!-- Optional. "Refs #123" if this enables a follow-up. -->
Refs #

## Scope

<!-- What's in: -->

<!-- What's deliberately not in (e.g., "I left module Y alone even though it has the same issue — separate PR"): -->

## Behavior change

> **This PR should not change observable behavior.** If it does, this is the wrong template.

- [ ] No public API changes
- [ ] No changes to inputs/outputs of affected functions
- [ ] No changes to database schema, queries, or stored data
- [ ] No changes to logs, metrics, or external side effects

<!-- If any box is unchecked, explain the change and consider whether this should be a feature/bug PR instead. -->

## How I verified no behavior change

<!-- Pick what applies and be specific. Examples: -->
<!-- - "Existing test suite passes with no modifications" -->
<!-- - "Ran the affected endpoint against staging with N sample requests, diffed responses, zero diff" -->
<!-- - "Snapshot tests unchanged" -->

## Testing

- [ ] All existing tests pass without modification
- [ ] Any test changes are purely structural (renames, moves, no logic changes)

<!-- If you changed test logic, explain why — that's a yellow flag for a refactor. -->

## Risk

<!-- Refactors are usually low-risk in theory and surprisingly risky in practice. Note anything reviewers should look at extra carefully — shared code paths, anything touching concurrency, anything in a hot path. -->
