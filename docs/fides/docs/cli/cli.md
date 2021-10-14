# Fidesctl CLI

---

`fidesctl` is an interactive shell that drives the fides functionality. If you're running fides in a  Docker container, you launch the `fidesctl` shell by `cd`ing to your `fides` root directory and running `make cli`.

```bash
$ cd <your-fides-root>
$ make cli
```

When it's finished,  `make cli` shows you a success message, `cd`s into the `fidesctl` directory, and presents you with the Docker prompt. Notice that the prompt includes your current working directory within the Docker container.

```bash
 ⠿ Container fides-fidesctl-db-1  Running   0.0s //success message
root@f76b4a7af333:/fides/fidesctl# //prompt
```

You can then use the `fidesctl` command line interface commands. The commands are provided as arguments to the `fidesctl` program. For example, to run the `init-db` command, you do this:

```bash
root@f76b4a7af333:/fides/fidesctl# fidesctl init-db
```

All `fidesctl` commands return 0 upon success.

## Commands

The `fidesctl` commands are listed below. Follow the link to the manual page for more information about a particular command.

* [`ping`](ping) determines if the fides API host is ready to receive messages.

* [`init-db`](init-db) launches your fides  database and initializes it with default resources definitions.

* [`apply`](apply) applies a set of manifest files to your fides database.

* [`reset-db`](reset-db) removes the previously-applied manifest data from your fides database. To re-constitute the data, you have to re-run `apply`.


* [`evaluate`](evaluate) [-k,--fides-key] [-m, --message] [--dry] runs your privacy policies and announces the results.
* `fidesctl get <resource_type> <fides_key>` - Looks up a specific resource on the server by its type and `fides_key`.
* `fidesctl ls <resource_type>` - Shows a list of all resources of a certain type that exist on the server.
* `fidesctl reset-db` - Tears down the database, erasing all data.
* `fidesctl version` - Shows the version of Fides that is installed.
* `fidesctl view-config`- Show a JSON representation of the config that Fidesctl is using.
