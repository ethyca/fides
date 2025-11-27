# PR Summary

## Create PR
Use the template found in `.github/pull_request_template.md` to provide a summary of the provided @Branch.

- Be as concise as possible with the summary, but be sure to fill out the exact template entirely.
- In the description, avoid phrases like "In this PR..." or "This PR," just start with the verb.
- In the summary, ignore code formatting or general code clean up changes.
- Do not include running tests as part of the Steps to Confirm, those will run automatically as part of the PR.

Provide a link to a GitHub URL with the body of the PR template and title as query parameters. The body should be in Markdown code format, patterned after the template.

- The format is: `https://github.com/ethyca/fides/compare/main...{branch}?quick_pull=1&title={title}&body={body}`. Make this link clickable, not copyable. Take care to ensure the URL encoding doesn't get mangled in the link. Be sure to include backticks encoded as %60 instead of stripping them from the description.
  - Key parameters:
    - quick_pull=1 - Opens the PR creation form
    - title= - URL-encoded PR title
    - body= - URL-encoded PR description (supports markdown with %0A for newlines)

- The issue can usually be derived from the branch name, it's a Jira ticket with prefix "ENG-" (eg. `Ticket [ENG-1234]`)

## Add the changelog
In addition to returning that markdown response, provide a concise, one-liner summary for the CHANGELOG no longer than about 85 characters or about 15 words max.
- It's ok to suggest multiple entries for large PRs, but each entry should be a short one-liner.
- Do not prefix the changelog entry with anything, start with a verb in the past tense (eg. "Added...", "Updated..." etc.)
- Add the changelog to the appropriate spot in the CHANGELOG.md file in the root. Make sure it always ends up in the "Unreleased" section.
- Do not put placeholders or anything for the PR link, it will be added manually once the PR is created.
