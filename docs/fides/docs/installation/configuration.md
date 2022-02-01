# Configuration

Fidesctl supports two methods of configuration. The first is via a toml file, and the second is via environment variables. They can also be used in tandem, with the environment variables overriding the toml configuration values.

By default the fidesctl CLI doesn't require a config file and will instead leverage the default values. These are very likely to be wrong however so it is recommended to always configure your settings properly.

## Configuration file

After initializing fidesctl, a default configuration file will be generated and placed within the `.fides` directory. Here's an example of a fidesctl configuration file:

```toml title="fidesctl.toml"
# Need to include other variables here
[api]
database_url = "postgres:fidesctl@fidesctl-db:5432/fidesctl"
log_destination = ""
log_level = 20
log_serialization = ""

[cli]
server_url = "http://localhost:8080"

[user]
analytics = true
```

By default fidesctl will look for a `fidesctl.toml` configuration file in the following places:

1. At the path specified using the config file argument passed through the CLI
1. At the path specified by the `FIDESCTL_CONFIG_PATH` environment variable
1. In a `.fides` directory within the current working directory
1. In a `.fides` directory within the user's home directory

## Environment Variables

To configure environment variables for fidesctl, the following pattern is used:

```sh
FIDESCTL__<SECTION>__<VAR_NAME>
```

For example, if we want to set the `server_url` on a Linux machine we could use:

```sh
export FIDESCTL__CLI__SERVER_URL="http://localhost:8080"
```
