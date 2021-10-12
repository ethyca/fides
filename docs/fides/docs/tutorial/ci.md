# Integrate your CI
_In this section, we'll reference a few examples and best practices for setting up your CI._

(TODO: rewrite)

Fides is meant to be a part of your CI pipeline jobs in order to enforce your organization's privacy policy on data before software is released to the world. We recommend setting up 2 different events to trigger during a CI pipeline run. 

## Repository Structure
Within your organization, you'll author manifest files and add these to the version control repositories alongside your source code, tests, etc. Each of these individual projects can then publish their manifests to the Fidesctl server via the API:
![Fides Manifest Workflow](../img/Manifest_Flow.svg)


## Pull Request
![Fides CI Workflow](../img/CI_Workflow.svg)
1. Set up a new CI workflow that gets triggered whenever a system or registry file gets changed within a pull request.
2. Configure the new workflow to run `fidesctl evaluate --dry fides_manifests/` when it gets triggered.
3. The command will trigger a non-zero exit if the evaluation fails.

Use the result of this job to determine whether or not a system change is safe to merge or not. If the command fails, check the error messages to see why the evaluation failed.

## Merge Event

1. Set up a new CI workflow that gets triggered whenever something in your manifests directory changes and the branch gets merged to the main branch.
1. Configure the new workflow to run two few jobs:
    1. `fidesctl apply fides_manifest/`
    1. `fidesctl evaluate system <fides_key>`

This will apply all of your manifests to the API and then evaluate the current state of your system on the main branch.

## Additional Resources

We have compiled a few reference implementations for some popular CI tools, which you can find here.

(TODO: provide examples)