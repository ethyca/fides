# Tutorial

This tutorial walks you through the process of getting up and running with Fides.

## Getting Started

Use either the [Docker](getting_started/docker.md) or [Local](getting_started/local.md) guide to get Fides up and running on your machine.

## Writing Manifest Files

The next critical step is to write the manifest files that describe privacy using the Fides ontology. Manifest files are written in YAML and are used to create objects within the Fides database via the FidesAPI.

For a set of example manifests see the [Fides Objects](fides_objects.md) page.

First create a directory for the manifests to live in:

`mkdir fides_manifests/`

Next, we need to define a Policy and a System, as those are the bare minimum objects that Fides requires.

## Applying Manifest Files

Once all of the required non-system manifest files have been defined, they can be sent to the server using Fidesctl. The command for this is:

`fidesctl apply <directory>`

This will load all files ending in either `.yaml` or `yml` and determines whether each object needs to be created, updated, or nothing needs to be done (the object exists on the server and there hasn't been a change). Any file formatting issues within the manifests will be caught and shown to the user. _This directory should not contain the system manifest, since it should be evaluated before submission!_

## Evaluatation

System manifests have a slightly different workflow as they are also meant to be incorporated into CI pipelines.

Use the following command to verify that your system is valid without creating it (safe to do in branches):

`fidesctl dry_evaluate <system_manifest> <fides_key>`

If that command shows passing, then it is safe to apply the system upon merge:

`fidesctl apply <system_manifest>`

## Setting up CI/CD

* Run dry eval locally
* CI pipeline to do `fidesctl dry_evaluate <system>`
* Apply manifests on merge
