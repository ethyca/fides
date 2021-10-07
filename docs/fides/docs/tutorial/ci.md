# Getting integrated with your CI tools
_In this section, we'll reference a few examples and best practices for setting up your CI._

Fides is meant to be a part of your CI pipeline jobs in order to enforce your organization's privacy policy on data before software is released to the world. We recommend setting up 2 different events to trigger during a CI pipeline run. 

## Pull Request

    1. Set up a new CI workflow that gets triggered whenever a system or registry file gets changed within a pull request.
    1. Configure the new workflow to run `fidesctl dry-evaluate fides_manifests/ <fides_key>` when it gets triggered.
    1. The command will trigger a non-zero exit if the evaluation fails.

    Use the result of this job to determine whether or not a system change is safe to merge or not. If the command fails, check the error messages to see why the evaluation failed.

## Merge Event

    1. Set up a new CI workflow that gets triggered whenever something in your manifests directory changes and the branch gets merged to the main branch.
    1. Configure the new workflow to run two few jobs:
        1. `fidesctl apply fides_manifest/`
        1. `fidesctl evaluate system <fides_key>`

    This will apply all of your manifests to the API and then evaluate the current state of your system on the main branch.

## Additional Resources

We have compiled a few reference implementations for some popular CI tools, which you can find here.
