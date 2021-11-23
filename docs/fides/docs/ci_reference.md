# CI/CD Reference

Fidesctl is primarily a tool designed to integrate with your CI pipeline configuration. You should plan to implement at least two CI actions:

1. `fidesctl evaluate --dry <resource_dir>`
    - Run against the latest commit on code changesets (pull requests, merge requests, etc.)
    - Checks if code changes will be accepted, without also applying changes to the fidesctl server
2. `fidesctl evaluate <resource_dir>`
    - Run against commits representing merges into the default branch
    - Synchronizes the latest changes to the fidesctl server

The following code snippets are meant only as simple example implementations, to illustrate how you might integrate fidesctl using various popular CI pipline tools. Always inspect, understand, and test your production CI configuration files.

## GitHub Actions

```yaml title="<code>.github/workflows/fidesctl_ci.yml</code>"
name: Fidesctl CI

# Only check on Pull Requests that target main
on:
  pull_request:
    branches:
      - main
    paths: # Only run checks when the resource files change or the workflow file changes
      - fides_resources/**
      - .github/workflows/fidesctl_ci.yml

jobs:
  fidesctl_ci:
    runs-on: ubuntu-latest
    container:
      image: ethyca/fidesctl:latest
    steps:
      - name: Dry Evaluation
        uses: actions/checkout@v2
        run: fidesctl evaluate --dry fides_resources/
        env:
          FIDESCTL__CLI__SERVER_URL: "https://fidesctl.privacyco.com"
```

```yaml title="<code>.github/workflows/fidesctl_cd.yml</code>"
name: Fidesctl CD

# Run the check every time a new commit hits the default branch
on:
  push:
    branches:
      - main
    tags:
      - "*"

jobs:
  fidesctl_cd:
    runs-on: ubuntu-latest
    container:
      image: ethyca/fidesctl:latest
    steps:
      - name: Evaluation
        uses: actions/checkout@v2
        run: fidesctl evaluate fides_resources/
        env:
          FIDESCTL__CLI__SERVER_URL: "https://fidesctl.privacyco.com"
```

## GitLab CI

```yaml title="<code>.gitlab-ci.yml</code>"
stages:
  - test
  - deploy

variables: &global-variables
  FIDESCTL__CLI__SERVER_URL: "https://fidesctl.privacyco.com"

fidesctl-ci:
  stage: test
  image: ethyca/fidesctl
  script: fidesctl evaluate --dry fides_resources/
  only:
    if: '$CI_PIPELINE_SOURCE = merge_request_event'
    changes:
      - fides_resources/**
      - .gitlab-ci.yml
  variables:
    <<: *global-variables

fidesctl-cd:
  stage: deploy
  image: ethyca/fidesctl
  script: fidesctl evaluate fides_resources/
  if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
  variables:
    <<: *global-variables
```
