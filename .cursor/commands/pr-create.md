# PR Summary

## Create PR
Use the template found in `.github/pull_request_template.md` to create a pull request of the provided @Branch.

- Be as concise as possible, but be sure to fill out the exact template entirely.
- In the description, avoid phrases like "In this PR..." or "This PR," just start with the verb.
- In the description and code changes sections, do not include information about code formatting or general code clean up changes.
- Do not include running tests as part of the Steps to Confirm, those will run automatically as part of the PR.
- The issue can usually be derived from the current branch name, it's a Jira ticket with prefix "ENG-" (eg. `Ticket [ENG-1234]`)
- If `acli` is available, use `acli jira workitem view [key]` cli command to get more information about the issue.
- If `gh` is available, use `gh pr create -d --title "[title]" --body "[body]"` cli command to create the PR in draft mode. The body should be in Markdown code format, patterned after the template.
- If `gh` is not available, provide a link to a GitHub URL with the body of the PR template and title as query parameters.
  - The format is: `https://github.com/ethyca/fides/compare/main...{branch}?quick_pull=1&title={title}&body={body}`. Make this link clickable, not copyable. Take care to ensure the URL encoding doesn't get mangled in the link. Be sure to include backticks encoded as %60 instead of stripping them from the description.
    - Key parameters:
      - quick_pull=1 - Opens the PR creation form
      - title= - URL-encoded PR title
      - body= - URL-encoded PR description (supports markdown with %0A for newlines)

## Add the changelog entry
In addition to returning that markdown response, create a changelog fragment file for the PR.

- Create a YAML file in the `changelog/` directory (use `.yaml` or `.yml` extension)
- Name the file using the PR number (e.g., `1234.yaml` or `pr-1234.yaml`) or a descriptive slug (e.g., `add-feature-name.yaml`)
- Use `changelog/TEMPLATE.yaml` as a reference for the format
- Provide a concise, one-liner description no longer than about 85 characters or about 15 words max
- Start the description with a verb in the past tense (e.g., "Added...", "Updated...", "Fixed..." etc.)
- Choose the appropriate `type` from: Added, Changed, Developer Experience, Deprecated, Docs, Fixed, Removed, Security
- If `gh` is used to create the PR, include the PR number in the `pr` field. If a URL was created instead, leave `pr` empty or omit it (it can be added later)
- Add `labels` if applicable: `["high-risk"]` for high-risk changes, `["db-migration"]` for database migrations, or `["high-risk", "db-migration"]` for both
- The changelog entry will be automatically compiled into `CHANGELOG.md` during the release process
- It's ok to suggest multiple fragment files for large PRs, but each entry should be a short one-liner
