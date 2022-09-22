# CI/CD Overview

Fides provides a CLI for integrating with your existing CI pipeline configurations. These commands are designed to help evaluate code changes against defined Fides [Policies](./guides/policies.md), and flag developers in advance if any updates or merges are no longer in compliance.
## Implementation
To integrate Fides with your CI pipeline, you should plan to implement at least two commands in your CI actions:

1. `fides evaluate --dry <resource_dir>`
    - `evaluate --dry` checks if code changes will be accepted **without** pushing those changes to the Fides server.
    - Run this against the latest commit on code changesets (pull requests, merge requests, etc).
2. `fides evaluate <resource_dir>`
    - `evaluate` synchronizes the latest changes to the Fides server.
    - Run this against commits representing merges into the default branch to keep your server in sync.

## Example Integrations

The following code snippets are meant as simple example implementations, and illustrate Fides can integrate with various popular CI pipeline tools. They are not designed for immediate production use.

!!! Tip "Always inspect, understand, and test your production CI configuration files."

### GitHub Actions

```yaml title="<code>.github/workflows/fides_ci.yml</code>"
name: Fides CI

# Only check on Pull Requests that target main
on:
  pull_request:
    branches:
      - main
    paths: # Only run checks when the resource files change or the workflow file changes
      - .fides/**
      - .github/workflows/fides_ci.yml

jobs:
  fides_ci:
    runs-on: ubuntu-latest
    container:
      image: ethyca/fides:latest
    steps:
      - name: Dry Evaluation
        uses: actions/checkout@v2
        run: fides evaluate --dry .fides/
        env:
          FIDES__CLI__SERVER_HOST: "fides.privacyco.com"
```

```yaml title="<code>.github/workflows/fides_cd.yml</code>"
name: Fides CD

# Run the check every time a new commit hits the default branch
on:
  push:
    branches:
      - main
    tags:
      - "*"

jobs:
  fides_cd:
    runs-on: ubuntu-latest
    container:
      image: ethyca/fides:latest
    steps:
      - name: Evaluation
        uses: actions/checkout@v2
        run: fides evaluate .fides/
        env:
          FIDES__CLI__SERVER_HOST: "fides.privacyco.com"
```
___
### GitLab CI

```yaml title="<code>.gitlab-ci.yml</code>"
stages:
  - test
  - deploy

variables: &global-variables
  FIDES__CLI__SERVER_HOST: "fides.privacyco.com"

fides-ci:
  stage: test
  image: ethyca/fides
  script: fides evaluate --dry .fides/
  only:
    if: '$CI_PIPELINE_SOURCE = merge_request_event'
    changes:
      - .fides/**
      - .gitlab-ci.yml
  variables:
    <<: *global-variables

fides-cd:
  stage: deploy
  image: ethyca/fides
  script: fides evaluate .fides/
  if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
  variables:
    <<: *global-variables
```
___
### Jenkins

```groovy title="<code>Jenkinsfile</code> (Declarative Syntax)"
pipeline {
  agent {
    docker {
      image 'ethyca/fides:latest'
    }
  }
  stages {
    stage('test'){
      environment {
          FIDES__CLI__SERVER_HOST: 'fides.privacyco.com'
      }
      steps {
        sh 'fides evaluate --dry .fides/'
      }
      when {
        anyOf {
          changeset '.fides/**'
          changeset 'Jenkinsfile'
        }
        changeRequest()
      }
    }
    stage('deploy') {
      environment {
          FIDES__CLI__SERVER_HOST: 'fides.privacyco.com'
      }
      steps {
        sh 'fides evaluate .fides/'
      }
      when {
        branch 'main'
      }
    }
  }
}
```
___
### CircleCI

```yaml title="<code>.circleci/config.yml</code>"
version: 2.1

executors:
  fides:
    docker:
      - image: ethyca/fides:latest
        environment:
          FIDES__CLI__SERVER_HOST: 'fides.privacyco.com'

jobs:
  fides-evaluate-dry:
    executor: fides
    steps:
      - run: fides evaluate --dry .fides/

  fides-evaluate:
    executor: fides
    steps:
      - run: fides evaluate .fides/

workflows:
  version: 2
  test:
    jobs:
      - fides-evaluate-dry:
          filters:
            branches:
              ignore: main

  deploy:
    jobs:
      - fides-evaluate:
          filters:
            branches:
              only: main
```

### Azure Pipelines

```yaml title="<code>.azure-pipelines.yml</code>"
# Trigger a dry run of the evaluate job on pull requests that target main
pr:
  - main

jobs:
  - job: "fides_evaluate_dry"
    pool:
      vmImage: ubuntu-latest
    container:
      image: ethyca/fides:latest
    steps:
      - checkout: self
      - script: fides evaluate --dry .fides/
        displayName: "Fides Dry Evaluation"


# Trigger the evaluate job on commits to the default branch
trigger: 
  - main

jobs:
  - job: "fides_evaluate"
    pool:
      vmImage: ubuntu-latest
    container:
      image: ethyca/fides:latest
    steps:
      - checkout: self
      - script: fides evaluate .fides/
        displayName: "Fides Evaluation"
```
