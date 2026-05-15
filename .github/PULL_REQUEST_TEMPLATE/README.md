# PR Templates

This folder holds our PR templates. Pick the one that best fits the change. **If a change spans multiple categories, pick the one that carries the most reviewer risk** — usually `bug` > `feature` > `refactor` > `chore`.

## When to use which

| Template | Use when… |
|---|---|
| [`bug.md`](./bug.md) | Fixing incorrect behavior. There's a reproducible problem (reported or discovered) and this PR makes it stop happening. |
| [`feature.md`](./feature.md) | Adding new user-facing or API-facing capability. Net-new behavior, not changing existing behavior. |
| [`refactor.md`](./refactor.md) | Restructuring code with **no intended behavior change**. If behavior changes, it's a bug fix or feature, not a refactor. |
| [`chore.md`](./chore.md) | Dependency bumps, build/CI/tooling changes, config tweaks, lint fixes, formatting, non-code housekeeping. |
| [`revert.md`](./revert.md) | Reverting a previously merged PR. Use this even if GitHub auto-generates a revert — replace the auto body with this template. |
| [`release.md`](./release.md) | Tracking a release. **This PR is never merged** — it exists for traceability and to hold the release checklist. Don't use this template for normal changes that happen to be in a release branch. |

## Notes for Claude (and humans)

- **Fill in every section that applies. Delete sections that genuinely don't.** Empty checkboxes are fine; empty narrative sections are noise.
- **Inline hints are in HTML comments** (`<!-- like this -->`) — strip them before submitting.
- **Linked issues use GitHub keywords** (`Fixes #123`, `Closes #123`, `Refs #123`) so they auto-close on merge where appropriate. Use `Refs` when the PR is related but shouldn't close the issue.
- **Screenshots / recordings**: if there's any UI change, include before/after. For API changes, a sample request/response pair counts.
- **`How to test this` is for the reviewer**, not the author. Numbered steps, setup notes, expected outcome. Present on `bug`, `feature`, and `revert` templates. Delete the section only if there is genuinely nothing to verify by hand (e.g. fully covered by an automated regression test with no user-observable surface).
- **`Testing` is for the author** — what you added/ran, not table-stakes "I ran the suite." "I ran the tests" is not testing evidence; new tests added, scenarios covered manually, and what you deliberately didn't test are.
- **`release.md` is human-driven.** The release checklist is meant to be worked through by a human release owner. If you're a Claude skill opening a PR, you almost certainly want one of the other five templates — not this one.

## URL shortcut

You can preselect a template by appending `?template=bug.md` (etc.) to the compare URL:

```
https://github.com/<org>/<repo>/compare/main...my-branch?quick_pull=1&template=bug.md
```

When opening PRs via the GitHub MCP (`mcp__github__create_pull_request`), the GitHub API, or `gh`, pass the chosen template's filled-in body directly as the `body` / `--body` argument.
