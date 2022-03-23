# CI/CD Overview

## 
Fidesctl is primarily designed to integrate with your existing CI pipeline configurations. Common implementations include:

* Github Actions
* Gitlab CI
* Jenkins
* CircleCI
* Azure Pipelines
* AWS CodePipeline
* Bitbucket
* Bamboo
* Team City

Implementing Fidesctl is possible in nearly any CI pipeline, including those not listed. 


## Implementation
To integrate Fidesctl with your CI pipeline, you should plan to implement at least two CI actions:

1. `fidesctl evaluate --dry <resource_dir>`
    - `evaluate --dry` checks if code changes will be accepted without applying those changes to the fidesctl server.
    - Run this against the latest commit on code changesets (pull requests, merge requests, etc).
2. `fidesctl evaluate <resource_dir>`
    - `evaluate` synchronizes the latest changes to the fidesctl server.
    - Run this against commits representing merges into the default branch.

[Implementation examples](./examples.md) are also available for a variety of CI tools.