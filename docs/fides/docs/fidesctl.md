# Fidesctl

Fidesctl wraps the functionality of the Fides Server into a CLI tool to be used by either engineers or within CI/CD pipelines.

## Commands

* `fidesctl ping` - Pings the server to make sure that a connection can be established.
* `fidesctl find <object_type> <fides_key>` - Looks up a specific object on the server by its type and `fides_key`.
* `fidesctl show <object_type>` - Shows a list of objects of a certain type that exist on the server.
* `fidesctl apply <manifest_dir>` - Creates or Updates objects found within the YAML files at the specified path.
* `fidesctl dry_evaluate <manifest_dir> <fides_key>` - Sends a System or Registry to the server to be evaluated without creating or modifying the object on the server.
* `fidesctl evaluate [system|registry] <fides_key>` - Runs an evaluation on an existing System or Registry.
