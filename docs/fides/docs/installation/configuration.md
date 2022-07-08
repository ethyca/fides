# Configuration

Fidesctl supports two methods of configuration. The first is via a toml file, and the second is via environment variables. They can also be used in tandem, with the environment variables overriding the toml configuration values.

By default the fidesctl CLI doesn't require a config file and will instead leverage the default values. These are very likely to be wrong however so it is recommended to always configure your settings properly.


## Configuration file

After initializing fidesctl, a default configuration file will be generated and placed within the `.fides` directory. Here's an example of a default fidesctl configuration file:



```toml title="fidesctl.toml"
[api]
database_user = "postgres"
database_password = "fidesctl"
database_host = "fidesctl-db"
database_port = "5432"
database_name = "fidesctl"

# Logging
log_destination = ""
log_level = INFO
log_serialization = ""

[cli]
local_mode = False
server_host = "localhost"
server_port = 8080
server_protocol = "http"
analytics_id = ""

[user]
encryption_key = "test_encryption_key"
analytics_opt_out = false
```

To better describe the various configuration options, the following tables describe each available option, grouped by section:

=== "API Section"

    | Name | Type | Default | Description |
    | :----: | :----: | :-------: | :-----------: |
    | database_user | String | postgres | The username of the Postgres account. |
    | database_password | String | fidesctl | The password of the Postgres account. |
    | database_host | String | fidesctl-db | The hostname of the Postgres database server. |
    | database_port | String | 5432 | The port of the Postgres database server. |
    | database_name | String | fidesctl | The name of the Postgres database. |
    | test_database_name | String | ""| Used instead of the `database_name` when the `FIDESCTL_TEST_MODE` environment variable is set to `True`, to avoid overwriting production data. | |
    | log_destination | String | "" | The output location for log files. Accepts any valid file path. If left unset, log entries are printed to `stdout` and log files are not produced. |
    | log_level | Enum (String) | INFO | The minimum log entry level to produce. Also accepts: `TRACE`, `DEBUG`, `WARNING`, `ERROR`, or `CRITICAL` (case insensitive). |
    | log_serialization | Enum (String) | "" | The format with which to produce log entries. If left unset, produces log entries formatted using the internal custom formatter. Also accepts: `"JSON"` (case insensitive). |

=== "CLI Section"

    | Name | Type | Default | Description |
    | :----: | :----: | :-------: | :-----------: |
    | local_mode | Boolean | False | When set to `True`, forbids the fidesctl CLI from making calls to the fidesctl webserver. |
    | server_host | String | localhost | The hostname of the fidesctl webserver. |
    | server_protocol | String | http | The protocol used by the fidesctl webserver. |
    | server_port | Integer | | The optional port of the fidesctl webserver. |
    | analytics_id | String | "" | A fully anonymized unique identifier for the `fidesctl` CLI instance. |

=== "User Section"

    | Name | Type | Default | Description |
    | :----: | :----: | :-------: | :-----------: |
    | encryption_key | String | "" | An arbitrary string used to encrypt the user data stored in the database. Encryption is implemented using PGP. |
    | analytics_opt_out | Boolean | "" | When set to `true`, prevents sending anonymous analytics data to Ethyca. |


=== "Credentials Section"

The credentials section uses custom keys which can be referenced in certain commands. 

    | Name | Type | Default | Description |
    | :----: | :----: | :-------: | :-----------: |
    | my_postgres.connection_string | String | Required | Sets the connection_string for `my_postgres` database credentials |
    | my_aws.aws_access_key_id | String | Required | Sets the aws_access_key_id for `my_aws` credentials |
    | my_aws.aws_secret_access_key | String | Required | Sets the aws_secret_access_key for `my_aws` credentials |
    | my_aws.region_name | String | Required | Sets the region_name for `my_aws` credentials |
    | my_okta.orgUrl | String | Required | Sets the orgUrl for `my_okta` credentials |
    | my_okta.token | String | Required | Sets the token for `my_okta` credentials |

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
export FIDESCTL__CLI__SERVER_HOST="localhost"
export FIDESCTL__CLI__SERVER_PORT="8080"
export FIDESCTL__CLI__SERVER_PROTOCOL="http"
```
