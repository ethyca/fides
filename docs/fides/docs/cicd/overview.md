# CI/CD Overview

<<<<<<< HEAD
## 
Fidesctl is primarily designed to integrate with your existing CI pipeline configurations. Common implementations include:

* Github Actions
* Gitlab CI
* Jenkins
* CircleCI
* Azure Pipelines
=======
Fidesctl is primarily designed to integrate with your existing CI pipeline configurations, including:

* [Github Actions](./ci_reference.md#github-actions)
* [Gitlab CI](./ci_reference.md#gitlab-ci)
* [Jenkins](./ci_reference.md#jenkins)
* [CircleCI](./ci_reference.md#circleci)
* [Azure Pipelines](./ci_reference.md#azure-pipelines)
>>>>>>> 7f16cf8 (CI references docs reorganization (#262))
* AWS CodePipeline
* Bitbucket
* Bamboo
* Team City

<<<<<<< HEAD
Implementing Fidesctl is possible in nearly any CI pipeline, including those not listed. 
=======
However, Fidesctl is capable of integrating with nearly any CI tool, including those not listed. 
>>>>>>> 7f16cf8 (CI references docs reorganization (#262))


## Implementation
To integrate Fidesctl with your CI pipeline, you should plan to implement at least two CI actions:

1. `fidesctl evaluate --dry <resource_dir>`
    - `evaluate --dry` checks if code changes will be accepted without applying those changes to the fidesctl server.
    - Run this against the latest commit on code changesets (pull requests, merge requests, etc).
2. `fidesctl evaluate <resource_dir>`
    - `evaluate` synchronizes the latest changes to the fidesctl server.
    - Run this against commits representing merges into the default branch.

[Implementation examples](./ci_reference.md) are also available for a variety of CI tools.