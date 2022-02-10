# Configuration

Fidesctl supports two methods of configuration. The first is via a toml file, and the second is via environment variables. They can also be used in tandem, with the environment variables overriding the toml configuration values.

By default the fidesctl CLI doesn't require a config file and will instead leverage the default values. These are very likely to be wrong however so it is recommended to always configure your settings properly.


## Configuration file

After initializing fidesctl, a default configuration file will be generated and placed within the `.fides` directory. Here's an example of a default fidesctl configuration file:



```toml title="fidesctl.toml"
[api]
database_url = "postgres:fidesctl@fidesctl-db:5432/fidesctl"

# Logging
log_destination = ""
log_level = INFO
log_serialization = ""

[cli]
local_mode = False
server_url = "http://localhost:8080"

[user]
encryption_key = "test_encryption_key"
```

To better describe the various configuration options, the following tables describe each available option, grouped by section:

=== "API Section"

    | Name | Type | Default | Description |
    | :----: | :----: | :-------: | :-----------: |
    | database_url | String | postgres:fidesctl@fidesctl-db:5432/fidesctl | The PostgreSQL database connection string for the fidesctl database. __NOTE__: Do not include the driver here, fidesctl will do this for you. |
    | test_database_url | String | ""| If the `FIDESCTL_TEST_MODE` environment variable is set to `True`, the `test_database_url` is used instead of the `database_url` to avoid overwriting production data. |
    | log_destination | String | "" | The output location for log files. Accepts any valid file path. If left unset, log entries are printed to `stdout` and log files are not produced. |
    | log_level | Enum (String) | INFO | The minimum log entry level to produce. Also accepts: `TRACE`, `DEBUG`, `WARNING`, `ERROR`, or `CRITICAL` (case insensitive). |
    | log_serialization | Enum (String) | "" | The format with which to produce log entries. If left unset, produces log entries formatted using the internal custom formatter. Also accepts: `"JSON"` (case insensitive). |

=== "CLI Section"

    | Name | Type | Default | Description |
    | :----: | :----: | :-------: | :-----------: |
    | local_mode | Boolean | False | When to `True`, the CLI will never attempt to call out to a fidesctl webserver. |
    | server_url | String | "" | The URL for the fidesctl webserver that the CLI should connect to. |

=== "User Section"

    | Name | Type | Default | Description |
    | :----: | :----: | :-------: | :-----------: |
    | encryption_key | String | "" | The key used to encrypt the user's data stored in the database. |


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
