# Example Integrations

The following code snippets are meant as simple example implementations, and illustrate how you might integrate fidesctl using various popular CI pipline tools. Always inspect, understand, and test your production CI configuration files.

  - [GitHub Actions](#github-actions)
  - [GitLab CI](#gitlab-ci)
  - [Jenkins](#jenkins)
  - [CircleCI](#circleci)
  - [Azure Pipelines](#azure-pipelines)
  
---
## GitHub Actions

```yaml title="<code>.github/workflows/fidesctl_ci.yml</code>"
name: Fidesctl CI

# Only check on Pull Requests that target main
on:
  pull_request:
    branches:
      - main
    paths: # Only run checks when the resource files change or the workflow file changes
      - .fides/**
      - .github/workflows/fidesctl_ci.yml

jobs:
  fidesctl_ci:
    runs-on: ubuntu-latest
    container:
      image: ethyca/fidesctl:latest
    steps:
      - name: Dry Evaluation
        uses: actions/checkout@v2
        run: fidesctl evaluate --dry .fides/
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
        run: fidesctl evaluate .fides/
        env:
          FIDESCTL__CLI__SERVER_URL: "https://fidesctl.privacyco.com"
```
___
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
  script: fidesctl evaluate --dry .fides/
  only:
    if: '$CI_PIPELINE_SOURCE = merge_request_event'
    changes:
      - .fides/**
      - .gitlab-ci.yml
  variables:
    <<: *global-variables

fidesctl-cd:
  stage: deploy
  image: ethyca/fidesctl
  script: fidesctl evaluate .fides/
  if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
  variables:
    <<: *global-variables
```
___
## Jenkins

```groovy title="<code>Jenkinsfile</code> (Declarative Syntax)"
pipeline {
  agent {
    docker {
      image 'ethyca/fidesctl:latest'
    }
  }
  stages {
    stage('test'){
      environment {
        FIDESCTL__CLI__SERVER_URL = 'https://fidesctl.privacyco.com'
      }
      steps {
        sh 'fidesctl evaluate --dry .fides/'
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
        FIDESCTL__CLI__SERVER_URL = 'https://fidesctl.privacyco.com'
      }
      steps {
        sh 'fidesctl evaluate .fides/'
      }
      when {
        branch 'main'
      }
    }
  }
}
```
___
## CircleCI

```yaml title="<code>.circleci/config.yml</code>"
version: 2.1

executors:
  fidesctl:
    docker:
      - image: ethyca/fidesctl:latest
        environment:
          FIDESCTL__CLI__SERVER_URL: 'https://fidesctl.privacyco.com'

jobs:
  fidesctl-evaluate-dry:
    executor: fidesctl
    steps:
      - run: fidesctl evaluate --dry .fides/

  fidesctl-evaluate:
    executor: fidesctl
    steps:
      - run: fidesctl evaluate .fides/

workflows:
  version: 2
  test:
    jobs:
      - fidesctl-evaluate-dry:
          filters:
            branches:
              ignore: main

  deploy:
    jobs:
      - fidesctl-evaluate:
          filters:
            branches:
              only: main
```
___
## Azure Pipelines

```yaml title="<code>.azure-pipelines.yml</code>"
# Trigger a dry run of the evaluate job on pull requests that target main
pr:
  - main

jobs:
  - job: "fidesctl_evaluate_dry"
    pool:
      vmImage: ubuntu-latest
    container:
      image: ethyca/fidesctl:latest
    steps:
      - checkout: self
      - script: fidesctl evaluate --dry .fides/
        displayName: "Fidesctl Dry Evaluation"


# Trigger the evaluate job on commits to the default branch
trigger: 
  - main

jobs:
  - job: "fidesctl_evaluate"
    pool:
      vmImage: ubuntu-latest
    container:
      image: ethyca/fidesctl:latest
    steps:
      - checkout: self
      - script: fidesctl evaluate .fides/
        displayName: "Fidesctl Evaluation"
```
