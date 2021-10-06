# Fidesctl CLI

---

The Fidesctl CLI wraps the entire functionality of Fidesctl into a few succint commands.

## Commands

This is a non-exhaustive list of available Fidesctl CLI commands:

* `fidesctl apply <manifest_dir> [--dry] [--diff]` - Creates or Updates resources found within the YAML file(s) at the specified path.
* `fidesctl evaluate [-k,--fides-key] [-m, --message] [--dry]` - Runs an evaluation of all policies, but a single policy can be specified using the `--fides-key` parameter.
* `fidesctl init-db` - Sets up the database by running all missing migrations.
* `fidesctl get <resource_type> <fides_key>` - Looks up a specific resource on the server by its type and `fides_key`.
* `fidesctl ls <resource_type>` - Shows a list of all resources of a certain type that exist on the server.
* `fidesctl ping` - Pings the API's healthcheck endpoint to make sure that it is reachable and ready for requests.
* `fidesctl reset-db` - Tears down the database, erasing all data.
* `fidesctl version` - Shows the version of Fides that is installed.
* `fidesctl view-config`- Show a JSON representation of the config that Fidesctl is using.
