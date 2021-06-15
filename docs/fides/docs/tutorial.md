# Tutorial

This tutorial walks you the fundamental functionality of Fides including major concepts and usage.

## Writing Manifest Files

Manifest files are written in `yaml` and are used create objects within the Fides database via the Fides server. They are read into Python models for use within Fidesctl before being converted to JSON and sent to the server.

There are examples of each type of object within the `fides_cli/sample/data/` sub-directory.

## Applying Manifest Files

Once all of the required manifest files have been defined, they can be sent to the server using Fidesctl. The command for this is:

`fidesctl apply <directory>`

This will load all files ending in either `.yaml` or `yml` and determines whether each one needs to be created, updated, or nothing needs to be done (the object exists on the server and there hasn't been a change). Any file formatting issues within the manifests will be caught and shown to the user.

## Evaluating Registries

With all of the manifests having been applied, it's time to evaluate the registry and confirm that everything is valid and safe. Use the following command:

`fidesctl evaluate <manifest_directory> [<registry_fidesKey>]>`

## Rectifying Manifest Errors

This step will potentially throw errors related to either invalid manifests (e.g. `dependent dataset doesn't exist`).
