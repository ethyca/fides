# Add a changelog entry

All fides PRs need a CHANGELOG entry that summarizes the implemented change.

- Create a YAML file in the `changelog/` directory (use `.yaml` or `.yml` extension)
- Name the file using the PR number (e.g., `1234.yaml` or `pr-1234.yaml`) or a descriptive slug (e.g., `add-feature-name.yaml`)
- Use `changelog/TEMPLATE.yaml` as a reference for the format
- Provide a concise, one-liner description no longer than about 85 characters or about 15 words max
- Start the description with a verb in the past tense (e.g., "Added...", "Updated...", "Fixed..." etc.)
- Choose the appropriate `type` from: Added (for new features), Changed (for updates to existing features), Developer Experience (for development-only changes), Deprecated (for deprecations), Docs (for docs updates), Fixed (for bugfixes), Removed (for removal of features), Security (for security-related changes)
- If you know the PR number, include it in the `pr` field, otherwise leave it empty and ask the user to fill it in.
- If GH_CLI is set to true, you can use the `gh` CLI to get the PR number (e.g., `gh pr view --json number`)
- Add `labels` if applicable: `["high-risk"]` for high-risk changes, `["db-migration"]` for changes that include database migrations
- The changelog entry will be automatically compiled into `CHANGELOG.md` during the release process
- It's ok to suggest multiple fragment files for large PRs, but each entry should be a short one-liner

