# Tutorial

This tutorial walks you the fundamental functionality of Fides including major concepts and usage.

## Writing Manifest Files

Manifest files are written in `yaml` and are used to create objects within the Fides database via the Fides server. They are read into Python models for use within Fidesctl before being converted to JSON and sent to the server.

System manifest files are intended to live with the application or code that it describes. All other manifests are intended to live in a separate directory or repository of Fides manifests.

For a set of example manifests see the [Manifests](manifests.md) page.

## Applying Non-System Manifest Files

Once all of the required non-system manifest files have been defined, they can be sent to the server using Fidesctl. The command for this is:

`fidesctl apply <directory>`

This will load all files ending in either `.yaml` or `yml` and determines whether each object needs to be created, updated, or nothing needs to be done (the object exists on the server and there hasn't been a change). Any file formatting issues within the manifests will be caught and shown to the user. _This directory should not contain the system manifest, since it should be evaluated before submission!_

## System Evaluatation and Creation

System manifests have a slightly different workflow as they are also meant to be incorporated into CI pipelines.

Use the following command to verify that your system is valid without creating it (safe to do in branches):

`fidesctl dry_evaluate <system_manifest> <fides_key>`

If that command shows passing, then it is safe to apply the system upon merge:

`fidesctl apply <system_manifest>`

## Registry Evaluation

With all of the manifests having been applied and systems evaluated and created, it's time to evaluate the registry and confirm that everything is valid and safe. Use the following command:

`fidesctl evaluate registry <registry_fidesKey>`
