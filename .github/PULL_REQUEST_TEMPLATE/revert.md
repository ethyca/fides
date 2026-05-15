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
