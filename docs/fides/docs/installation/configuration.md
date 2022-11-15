# Configuration

The Fides application configuration variables are provided in a `fides.toml` file. Fides will use the first config file it reads from the following locations, in order:

1. At the path specified using the config file argument passed through the CLI
1. At the path specified by the `FIDES__CONFIG_PATH` environment variable
1. In the current working directory
1. In the parent working directory
1. Two directories up from the current working directory
1. The parent directory followed by `/.fides`
1. The user's home (`~`) directory

Fides can also run exclusively via environment variables. These can be used in tandem with a `toml` configuration file, with the environment variables overriding the toml configuration values.

## Viewing your configuration

You can view the current configuration of your application via either the CLI or API

### CLI

To view your application configuration via the CLI, run:

```sh
fides view config
```

The output will look something like this:

```sh
fides> fides view config 
Loading config from: .fides/fides.toml
Directory './.fides' already exists.
Configuration file already exists: ./.fides/fides.toml
To learn more about configuring fides, see:
        https://ethyca.github.io/fides/installation/configuration/
----------
test_mode = false
is_test_mode = false
hot_reloading = false
dev_mode = false

[admin_ui]
enabled = true

[cli]
local_mode = false
analytics_id = "internal"
server_protocol = "http"
server_host = "localhost"
...
```

The output after the initial separator (`----------`) is valid TOML, and can be copy/pasted for reuse as a functioning config file.

For more information, see the [CLI docs](../cli.md).

### API

To view your application configuration via the CLI, run:

```sh
GET /api/v1/config
```

Fides will filter out any sensitive configuration variables. The full list of variables deemed safe to return is:

#### Postgres database

- `server`
- `user`
- `port`
- `db`
- `test_db`

#### Redis cache

- `host`
- `port`
- `charset`
- `decode_responses`
- `default_ttl_seconds`
- `db_index`

#### Security settings

- `cors_origins`
- `encoding`
- `oauth_access_token_expire_minutes`

#### Execution settings

- `task_retry_count`
- `task_retry_delay`
- `task_retry_backoff`
- `require_manual_request_approval`
- `masking_strict`

For more information, see the [API docs](../api/index.md).

## Configuration file

After initializing Fides, a default configuration file will be generated and placed within the `.fides` directory:

```toml title="fides.toml"
[database]
server = "fides-db"
user = "postgres"
password = "fides"
port = "5432"
db = "fides"

[logging]
level = "INFO"

[cli]
server_host = "localhost"
server_port = 8080
analytics_id = ""

[user]
analytics_opt_out = false

[redis]
host = "redis"
password = "testpassword"
port = 6379
charset = "utf8"
default_ttl_seconds = 604800
db_index = 0
enabled = true
ssl = false
ssl_cert_reqs = "required"

[security]
app_encryption_key = ""
cors_origins = [ "http://localhost", "http://localhost:8080", "http://localhost:3000", "http://localhost:3001",]
encoding = "UTF-8"
oauth_root_client_id = "adminid"
oauth_root_client_secret = "adminsecret"
drp_jwt_secret = "secret"
root_username = "root_user"
root_password = "Testpassword1!"

[execution]
masking_strict = true
require_manual_request_approval = false
task_retry_backoff = 1
subject_identity_verification_required = false
task_retry_count = 0
task_retry_delay = 1

[admin_ui]
enabled = true

```

## Configuration variable reference

The `fides.toml` file should specify the following variables:

#### Posgtres database

| Name | Type | Default | Description |
| :---- | :---- | :------- | :----------- |
| `user` | String | `postgres` | The database user with which to login to the application database. |
| `password` | String | `fides` | The password with which to login to the application database. |
| `server` | String | `fides-db` | The hostname of the Postgres database server. |
| `port` | String | `5432` | The port at which the Postgres database will be accessible. |
| `db` | String | `fides` | The name of the Postgres database. |
| `test_db` | String | `""` | Used instead of the `db` config when the `FIDES_TEST_MODE` environment variable is set to `True`, to avoid overwriting production data. |

#### Redis cache

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `host` | string | N/A | The network address for the application Redis cache. |
| `port` | int | `6379` | The port at which the application cache will be accessible. |
| `user` | string | N/A | The user with which to login to the Redis cache. |
| `password` | string | N/A | The password with which to login to the Redis cache. |
| `db_index` | int | N/A | The application will use this index in the Redis cache to cache data. |
| `connection_url` | string | N/A | A full connection URL to the Redis cache. If not specified, this URL is automatically assembled from the `host`, `port`, `password` and `db_index` specified above. |
| `default_ttl_seconds` | int | 604800 | The number of seconds for which data will live in Redis before automatically expiring. |
| `enabled` | bool | `True` | Whether the application's Redis cache should be enabled. Only set to false for certain narrow uses of the application. |

#### Logging

| Name | Type | Default | Description |
| :---- | :---- | :------- | :----------- |
| `destination` | String | `""` | The output location for log files. Accepts any valid file path. If left unset, log entries are printed to `stdout` and log files are not produced. |
| `level` | Enum (String) | `INFO` | The minimum log entry level to produce. Also accepts `TRACE`, `DEBUG`, `WARNING`, `ERROR`, or `CRITICAL` (case insensitive). |
| `serialization` | Enum (String) | `""` | The format with which to produce log entries. If left unset, produces log entries formatted using the internal custom formatter. Also accepts `"JSON"` (case insensitive). |

#### CLI

| Name | Type | Default | Description |
| :---- | :---- | :------- | :----------- |
| `local_mode` | Boolean | `False` | When set to `True`, forbids the Fides CLI from making calls to the Fides webserver. |
| `server_host` | String | `localhost` | The hostname of the Fides webserver. |
| `server_protocol` | String | `http` | The protocol used by the Fides webserver. |
| `server_port` | Integer | | The optional port of the Fides webserver. |
| `analytics_id` | String | `""` | A fully anonymized unique identifier that is automatically generated by the application and stored in the toml file. |

#### Security

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `app_encryption_key` | string | N/A | The key used to sign Fides API access tokens. |
| `cors_origins` | List[AnyHttpUrl] | N/A | A list of pre-approved addresses of clients allowed to communicate with the Fides application server. |
| `oauth_root_client_id` | string | N/A | The value used to identify the Fides application root API client. |
| `oauth_root_client_secret` | string | N/A | The secret value used to authenticate the Fides application root API client. |
| `oauth_access_token_expire_minutes` | int | `11520` | The time for which Fides API tokens will be valid. |
| `root_username` | string | None | If set, this can be used in conjunction with `root_password` to log in without first creating a user in the database. |
| `root_password` | string | None | If set, this can be used in conjunction with `root_username` to log in without first creating a user in the database. |
| `root_user_scopes` | list of strings | All available scopes | The scopes granted to the root user when logging in with `root_username` and `root_password`. |
| `subject_request_download_link_ttl_seconds` | int | `432000` | The number of seconds that a pre-signed download URL when using S3 storage will be valid. |
| `identity_verification_attempt_limit` | int | `3` | The number of identity verification attempts to allow. |

#### Execution

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
|`privacy_request_delay_timeout` | int | `3600` | The amount of time to wait for actions which delay privacy requests (e.g., pre- and post-processing webhooks). |
|`task_retry_count` | int | `0` | The number of times a failed request will be retried. |
|`task_retry_delay` | int | `1` | The delays between retries in seconds. |
|`task_retry_backoff` | int | `1` | The backoff factor for retries, to space out repeated retries. |
|`subject_identity_verification_required` | bool | `False` | Whether privacy requests require user identity verification. |
|`require_manual_request_approval` | bool | `False` | Whether privacy requests require explicit approval to execute. |
|`masking_strict` | bool | `True` | If set to `True`, only use UPDATE requests to mask data. If `False`, Fides will use any defined DELETE or GDPR DELETE endpoints to remove PII, which may extend beyond the specific data categories that configured in your execution policy. |
|`celery_config_path` | string | N/A | An optional override for the [Celery](#celery-configuration) configuration file path. |

#### User

| Name | Type | Default | Description |
| :---- | :---- | :------- | :----------- |
| `encryption_key` | String | `""` | An arbitrary string used to encrypt the user data stored in the database. Encryption is implemented using PGP. |
| `analytics_opt_out` | Boolean | `""` | When set to `true`, prevents sending anonymous analytics data to Ethyca. |

#### Credentials

The credentials section uses custom keys which can be referenced in certain commands.

| Name | Type | Description |
| :---- | :---- | :----------- |
| `my_postgres.connection_string` | String | Sets the `connection_string` for `my_postgres` database credentials |
| `my_aws.aws_access_key_id` | String | Sets the `aws_access_key_id` for `my_aws` credentials |
| `my_aws.aws_secret_access_key` | String | Sets the `aws_secret_access_key` for `my_aws` credentials |
| `my_aws.region_name` | String | Sets the `region_name` for `my_aws` credentials |
| `my_okta.orgUrl` | String | Sets the `orgUrl` for `my_okta` credentials |
| `my_okta.token` | String | Sets the `token` for `my_okta` credentials |

#### Admin UI

| Name | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `True` | Toggle whether the Admin UI is served from `/`. |

## Set environment variables

To configure environment variables for Fides, the following pattern is used:

```sh
FIDES__<SECTION>__<VAR_NAME>
```

For example, to set the `server_url` on a Linux machine:

```sh
export FIDES__CLI__SERVER_HOST="localhost"
export FIDES__CLI__SERVER_PORT="8080"
export FIDES__CLI__SERVER_PROTOCOL="http"
```

### Additional environment variables

The following environment variables are not included in the default `fides.toml` configuration, but may be set in your environment:

 ENV Variable | Default | Description |
|---|---|---|
| `FIDES__LOG_PII` | `False` | If `True`, PII values will display unmasked in log output. This variable should always be set to "False" in production systems.
| `FIDES__HOT_RELOAD` | `False` | If `True`, the Fides server will reload code changes without needing to restart the server. This variable should always be set to `False` in production systems.|
| `FIDES__DEV_MODE` | `False` | If `True`, the Fides server will log error tracebacks, and log details of third party requests. This variable should always be set to `False` in production systems.|
| `FIDES_CONFIG_PATH` | None | If this is set to a path, that path will be used to load `.toml` files first. Any .toml files on this path will override any installed .toml files. |
| `FIDES__DATABASE__SQLALCHEMY_DATABASE_URI` | None | An optional override for the URI used for the database connection, in the form of `postgresql://<user>:<password>@<hostname>:<port>/<database>`. |

## Celery configuration

Fides uses [Celery](https://docs.celeryq.dev/en/stable/index.html) for asynchronous task management.

The `celery.toml` file provided contains a brief configuration reference for managing Celery variables. By default, Fides will look for this file in the root directory of your application, but this location can be optionally overridden by specifying an alternate `celery_config_path` in your `fides.toml`.

For a full list of possible variable overrides, see the [Celery configuration](https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings) documentation.

```sh title="Example <code>celery.toml</code>"
default_queue_name = "fides"
broker_url = "redis://:testpassword@redis:6379/1"
result_backend = "redis://:testpassword@redis:6379/1"
```

 Celery Variable | Example | Description |
|---|---|---|
| `default_queue_name` | `fides` | A name to use for your Celery task queue. |
| `broker_url` | `redis://:testpassword@redis:6379/1`  | The datastore to use as a [Celery broker](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/), which maintains an ordered list of asynchronous tasks to execute. If not specified, Fides will default to the `connection_url` or Redis config values specified in your `fides.toml`.
| `result_backend` | `redis://:testpassword@redis:6379/1` | The [backend datastore](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/) where Celery will store results from asynchronously processed tasks. If not specified, Fides will default to the `connection_url` or Redis config values specified in your `fides.toml`.
