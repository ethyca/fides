# Tutorial

This tutorial walks you through the process of getting up and running with Fides.

## Getting Started

Use either the [Docker](getting_started/docker.md) or [Local](getting_started/local.md) guide to get Fides up and running on your machine.

## Writing Manifest Files

The next step is to write the manifest files that describe your privacy data usage with the Fides privacy ontology. Manifest files are written in YAML and are used to create and update objects within the Fides database via the FidesAPI.

First create a directory for the manifests to live in:

`mkdir fides_manifests/`

Next, you'll need to write a System manifest file and a Policy manifest file. These are the only two required objects for Fides to function. For an exhaustive set of example manifests see the [Fides Objects](fides_objects.md) page.

## Applying Manifest Files

Once you've finished writing your manifest files, it's time to apply them to the server. This is done with a single `fidesctl` command that handles both creating _and_ updating objects in the Fides database. If an object with the same type and fidesKey already exists, that object will be updated.

If we assume the same directory name as before for where our manifests are located, the command would be:

`fidesctl apply fides_manifests/`

This will load all files ending in either `.yaml` or `.yml` within that directory. Any file formatting issues within the manifests will be caught and shown to the user.

## Evaluatation

Systems and Registries have a slightly different workflow as they are also designed to be incorporated into CI pipelines.

Now that you've created your initial manifest files via the `apply` command, it's time to evaluate if that initial system is compliant. Use the following command to evaluate your system:

`fidesctl evaluate system <fides_key>`

If that command returns a "PASS" evaluation, then you're now in a known-good state and ready to set up automated CI workflows to make sure your application stays compliant within each PR.

## Setting up CI/CD

To set up CI/CD for Fides evaluations, there are a few suggested steps to follow:

=== "Pull Request"

    1. Set up a new CI workflow that gets triggered whenever a system or registry file gets changed within a pull request
    1. Configure the new workflow to run `fidesctl dry-evaluate fides_manifests/ <fides_key>` when it gets triggered
    1. The command will trigger a non-zero exit if the evaluation fails

    Use the result of this job to determine whether or not a system change is safe to merge or not. If the command fails, check the error messages to see why the evaluation failed.

=== "Merge Event"

    1. Set up a new CI workflow that gets triggered whenever something in your manifests directory changes and the branch gets merged to the main branch
    1. Configure the new workflow to run two few jobs:
        1. `fidesctl apply fides_manifest/`
        1. `fidesctl evaluate system <fides_key>`

    This will apply all of your manifests to the API and then evaluate the current state of your system on the main branch.

## Next Steps

Congratulations, you've walked through all of the steps to get a simple but complete Fides instance running! Here are some next steps to continue building out your Fides instance:

1. Define Datasets
1. Create a Registry and assign systems to it
1. Add more Policy Rules or Policies
1. Extend the Privacy Classifiers as needed
