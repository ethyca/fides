# Fidesctl

Fidesctl wraps the functionality of the Fides Server into a CLI tool to be used by either engineers or within CI/CD pipelines.

## Commands

* `fidesctl apply <manifest_dir> [--dry] [--diff]` - Creates or Updates resources found within the YAML file(s) at the specified path.
* `fidesctl evaluate [-k,--fides-key] [-m, --message] [--dry]` - Runs an evaluation of all policies, but a single policy can be specified using the `--fides-key` parameter.
* `fidesctl find <resource_type> <fides_key>` - Looks up a specific resource on the server by its type and `fides_key`.
* `fidesctl ls <resource_type>` - Shows a list of resources of a certain type that exist on the server.
* `fidesctl ping` - Pings the server to make sure that a connection can be established.
* `fidesctl version` - Shows the version of Fides that is installed.
* `fidesctl view-config`- Show a JSON representation of the config that Fides is using.
