# CI Reference

Fidesctl is a CI/CD tool first and foremost. With that in mind, we've included example CI/CD files for GitHub Actions to give an idea of what it looks like to run Fidesctl as part of a software development workflow.

You should plan to implement two CI actions:

1. Run `fidesctl evaluate --dry <resource_dir>` on pull requests, to check if new code will be accepted without applying those changes to the server.
2. Run `fidesctl evaluate <resource_dir>` on commits to main, to synchronize the latest changes to the server.

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
