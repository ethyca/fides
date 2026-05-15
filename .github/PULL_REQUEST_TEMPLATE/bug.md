## Summary

<!-- One or two sentences: what was broken and what this PR does about it. -->

## Linked issues

<!-- Use "Fixes #123" to auto-close on merge. Use "Refs #123" for related context. -->
Fixes #

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
