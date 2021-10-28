# Fidesctl CLI Overview


`fidesctl` provides an interactive shell that drives the Fides functionality. If you run Fides in a  Docker container, you launch the `fidesctl` shell by `cd`ing to your `fides` root directory and running `make cli`.

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

In addition to the individual commands, `fidesctl` takes a set of options. The most important option is `--config-path` which lets you supply a file that configures the `fidesctl` environment.

### OPTIONS

**-f/--config-path _config_file_** 

Identifies a file that you can use to configure the `fidesctl` environment. For more information about the file, see **Fidesctl Configuration File**. To see the current configuration file, do `fidesctl view-config`.

**-v/--version** 

Prints the `fidesctl` version number.

**-h/--help**

Prints a synopsis of the `fidesctl` command. 
 

### COMMANDS


* `apply` creates and updates resource objects by reading a set of resource manifest files.
* `delete` deletes a resource.
* `evaluate` runs your policies against your data and announces the results.
* `generate-dataset` imports a database and converts it into Dataset objects.
* `get` prints information about a resource.
* `init-db` initializes and launches your resource database.
* `ls` lists the resources of a specific type.
* `parse` validates the taxonomy built from a set of resource manifest files.
* `ping` determines if the fides API host is ready to receive messages.
* `reset-db` removes the previously-applied manifest data from your resource database.
* `view-config` prints the `fidesctl` configuration settings as a JSON object.
* `webserver` starts the `fidesctl` API server.

