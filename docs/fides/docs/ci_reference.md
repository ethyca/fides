# CI/CD Reference

Fidesctl is primarily a tool designed to integrate with your CI pipeline configuration. You should plan to implement at least two CI actions:

1. `fidesctl evaluate --dry <resource_dir>`
    - Run against the latest commit on code changesets (pull requests, merge requests, etc.)
    - Checks if code changes will be accepted, without also applying changes to the fidesctl server
2. `fidesctl evaluate <resource_dir>`
    - Run against commits representing merges into the default branch
    - Synchronizes the latest changes to the fidesctl server

The following code snippets are meant only as simple example implementations, to illustrate how you might integrate fidesctl using various popular CI pipline tools. Always inspect, understand, and test your production CI configuration files.

Let's see what those look like for GitHub Actions:

```yaml
name: Fidesctl CI Check

# Only check on Pull Requests that target main
on:
  pull_request:
    branches:
      - main
    paths: # Only run checks when the resource files change or the workflow file changes
      - fides_resources/**
      - .github/workflows/fidesctl_ci.yaml

jobs:
  Fidesctl:
    runs-on: ubuntu-latest
    container:
      image: ethyca/fidesctl:latest

    steps:
      - uses: actions/checkout@v2

      - name: Dry Evaluation
        run: fidesctl evaluate --dry fides_resources/
        env:
          FIDESCTL__CLI__SERVER_URL: "https://fidesctl.privacyco.com"
```

```yaml
name: Fidesctl CD Check

# Run the checks every single time a new commit hits Main
on:
  push:
    branches:
      - main
    tags:
      - "*"

jobs:
  Fidesctl:
    runs-on: ubuntu-latest
    container:
      image: ethyca/fidesctl:latest

    steps:
      - uses: actions/checkout@v2

      - name: Evaluation
        run: fidesctl evaluate fides_resources/
        env:
          FIDESCTL__CLI__SERVER_URL: "https://fidesctl.privacyco.com"
```
