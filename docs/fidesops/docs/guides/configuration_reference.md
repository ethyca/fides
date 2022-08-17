# Application Configuration Reference


## How to configure the fidesops application

The fidesops application configuration variables are provided in the `fidesops.toml` file in `.toml` format. Fidesops will take the first config file it finds from the following locations:

- The location according to the `FIDESOPS__CONFIG_PATH` environment variable
- The current working directory (`./fidesops.toml`)
- The parent of the current working directory (`../fidesops.toml`)
- The user's home directory (`~/fidesops.toml`)

Fidesops is also able to be run exclusively from environment variables. For more information and examples, see [Deployment](../deployment.md#step-3-setup-fidesops-web-server).


## Configuration variable reference

The `fidesops.toml` file should specify the following variables:


| TOML Variable | ENV Variable | Type | Example | Default | Description |
|---|---|---|---|---|---|
| `port` | --- | int | 8080 | 8080 | The port at which the webserver will run.|
| Database Variables |---|---|---|---|---|
| `server` | `FIDESOPS__DATABASE__SERVER` | string | postgres.internal | N/A | The networking address for the fideops Postgres database server |
| `user` | `FIDESOPS__DATABASE__USER` | string | postgres | N/A | The database user with which to login to the fidesops application database |
| `password` | `FIDESOPS__DATABASE__PASSWORD` | string | apassword | N/A | The password with which to login to the fidesops application database |
| `port` | `FIDESOPS__DATABASE__PORT` | int | 5432 | 5432 | The port at which the fidesops application database will be accessible |
| `db` | `FIDESOPS__DATABASE__DB` | string | db | N/A | The name of the database to use in the fidesops application database |
| `enabled` | `FIDESOPS__DATABASE__ENABLED` | bool | True | True | Whether the application database should be enabled. Only set to false for certain narrow uses of the application that do not require a backing application database. |
| Redis Variables |---|---|---|---|---|
| `host` | `FIDESOPS__REDIS__HOST` | string | redis.internal | N/A | The networking address for the fidesops application Redis cache |
| `port` | `FIDESOPS__REDIS__PORT` | int | 6379 | 6379 | The port at which the fidesops application cache will be accessible |
| `user` | `FIDESOPS__REDIS__USER` | string | testuser | N/A | The user with which to login to the Redis cache |
| `password` | `FIDESOPS__REDIS__PASSWORD` | string | anotherpassword | N/A | The password with which to login to the fidesops application cache |
| `db_index` | `FIDESOPS__REDIS__DB_INDEX` | int | 0 | N/A | The fidesops application will use this index in the Redis cache to cache data |
| `connection_url` | `FIDESOPS__REDIS__CONNECTION_URL` | string | redis://:testpassword@redis:6379/0 | N/A | If not specified this URL is automatically assembled from the `host`, `port`, `password` and `db_index` specified above |
| `default_ttl_seconds` | `FIDESOPS__REDIS__DEFAULT_TTL_SECONDS` | int | 3600 | 604800 | The number of seconds for which data will live in Redis before automatically expiring |
| `enabled` | `FIDESOPS__REDIS__ENABLED` | bool | True | True | Whether the application's redis cache should be enabled. Only set to false for certain narrow uses of the application that do not require a backing redis cache. |
| Security Variables |---|---|---|---|---|
| `app_encryption_key` | `FIDESOPS__SECURITY__APP_ENCRYPTION_KEY` | string | OLMkv91j8DHiDAULnK5Lxx3kSCov30b3 | N/A | The key used to sign fidesops API access tokens |
| `cors_origins` | `FIDESOPS__SECURITY__CORS_ORIGINS` | List[AnyHttpUrl] | ["https://a-client.com/", "https://another-client.com"/] | N/A | A list of pre-approved addresses of clients allowed to communicate with the fidesops application server |
| `log_level` | `FIDESOPS__SECURITY__LOG_LEVEL` | string | INFO | N/A | The log level used for fidesops. Must be one of DEBUG, INFO, WARNING, ERROR, or CRITICAL |
| `oauth_root_client_id` | `FIDESOPS__SECURITY__OAUTH_ROOT_CLIENT_ID` | string | fidesopsadmin | N/A | The value used to identify the fidesops application root API client |
| `oauth_root_client_secret` | `FIDESOPS__SECURITY__OAUTH_ROOT_CLIENT_SECRET` | string | fidesopsadminsecret | N/A | The secret value used to authenticate the fidesops application root API client |
| `oauth_access_token_expire_minutes` | `FIDESOPS__SECURITY__OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | int | 1 | 11520 | The time period fidesops API tokens will be valid |
| Execution Variables |---|---|---|---|---|
|`privacy_request_delay_timeout` | `FIDESOPS__EXECUTION__PRIVACY_REQUEST_DELAY_TIMEOUT` | int | 3600 | 3600 | The amount of time to wait for actions delaying privacy requests, for example pre and post processing webhooks.
|`task_retry_count` | `FIDESOPS__EXECUTION__TASK_RETRY_COUNT` | int | 5 | 0 | The number of times a failed request will be retried
|`task_retry_delay` | `FIDESOPS__EXECUTION__TASK_RETRY_DELAY` | int | 20 | 1 | The delays between retries in seconds
|`task_retry_backoff` | `FIDESOPS__EXECUTION__TASK_RETRY_BACKOFF` | int | 2 | 1 | The backoff factor for retries, to space out repeated retries.
|`require_manual_request_approval` | `FIDESOPS__EXECUTION__REQUIRE_MANUAL_REQUEST_APPROVAL` | bool | False | False | Whether privacy requests require explicit approval to execute
|`masking_strict` | `FIDESOPS__EXECUTION__MASKING_STRICT` | bool | True | True | If masking_strict is True, we only use "update" requests to mask data. (For third-party integrations, you should define an `update` endpoint to use.)  If masking_strict is False, you are allowing fidesops to use any defined DELETE or GDPR DELETE endpoints to remove PII. In this case, you should define `delete` or `data_protection_request` endpoints for your third-party integrations.  Note that setting masking_strict to False means that data may be deleted beyond the specific data categories that you've configured in your Policy.
|`celery_config_path` | `FIDESOPS__EXECUTION__CELERY_CONFIG_PATH` | string | data/config/celery.toml | N/A | An optional override for the [Celery](#celery-configuration) configuration file path.
|`worker_enabled` | `FIDESOPS__EXECUTION__WORKER_ENABLED` | bool | True | True | By default, fidesops uses a dedicated [Celery worker](#celery-configuration) to process privacy requests asynchronously. Setting `worker_enabled` to `False` will run the worker on the same node as the webserver.
|Analytics |---|---|---|---|---|
|`analytics_opt_out` | `FIDESOPS__USER__ANALYTICS_OPT_OUT` | bool | False | False | Opt out of sending anonymous usage data to Ethyca to improve the product experience.
| Admin UI Variables|---|---|---|---|---|
|`enabled` | `FIDESOPS__ADMIN_UI__ENABLED` | bool | False | True | Toggle whether the Admin UI is served from `/`

### An example `fidesops.toml` configuration file

```
port = 8080

[database]
server = "db"
user = "postgres"
password = "a-password"
db = "app"
test_db = "test"
enabled = true

[redis]
host = "redis"
password = "testpassword"
port = 6379
charset = "utf8"
default_ttl_seconds = 3600
db_index = 0
enabled = true

[security]
app_encryption_key = "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"
cors_origins = [ "http://localhost", "http://localhost:8080", "http://localhost:3000", "http://localhost:3001",]
encoding = "UTF-8"
oauth_root_client_id = "fidesopsadmin"
oauth_root_client_secret = "fidesopsadminsecret"
log_level = "INFO"

[execution]
masking_strict = true
require_manual_request_approval = true
task_retry_count = 3
task_retry_delay = 20
task_retry_backoff = 2
worker_enabled = true
celery_config_path="data/config/celery.toml"


[root_user]
analytics_opt_out = false

[admin_ui]
enabled = true
```

Note: The configuration is case-sensitive, so the variables must be specified in `lowercase`.

### Additional environment variables

 ENV Variable | Default | Description |
|---|---|---|
| `FIDESOPS__LOG_PII` | False | If this is set to "True", pii values will display unmasked in log output. This variable should always be set to "False" in production systems.
| `FIDESOPS__HOT_RELOAD` | False | If "True", the fidesops server will reload code changes without you needing to restart the server. This variable should always be set to "False" in production systems.|
| `FIDESOPS__DEV_MODE` | False | If "True", the fidesops server will log error tracebacks, and log details of third party requests. This variable should always be set to "False" in production systems.|
| `FIDESOPS__CONFIG_PATH` | None | If this variable is set to a path, that path will be used to load .toml files first. That is, any .toml files on this path will override any installed .toml files. |
| `FIDESOPS__DATABASE__SQLALCHEMY_DATABASE_URI` | None | An optional override for the URI used for the database connection, in the form of `postgresql://<user>:<password>@<hostname>:<port>/<database>`. |
| `TESTING` | False | This variable does not need to be set - Pytest will set it to True when running unit tests, so we run against the test database. |

## Celery configuration

Fidesops uses [Celery](https://docs.celeryq.dev/en/stable/index.html) for asynchronous task management. 

The `celery.toml` file provided contains a brief configuration reference for managing Celery variables. By default, fidesops will look for this file in the root directory of your application, but this location can be optionally overridden by specifying an alternate `celery_config_path` in your `fidesops.toml`.

For a full list of possible variable overrides, see the [Celery configuration](https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings) documentation.

```sh title="Example <code>celery.toml</code>"
default_queue_name = "fidesops"
broker_url = "redis://:testpassword@redis:6379/1"
result_backend = "redis://:testpassword@redis:6379/1"
```

 Celery Variable | Example | Description |
|---|---|---|
| `default_queue_name` | `fidesops` | A name to use for your Celery task queue. |
| `broker_url` | redis://:testpassword@redis:6379/1  | The datastore to use as a [Celery broker](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/), which maintains an ordered list of asynchronous tasks to execute. If not specified, fidesops will default to the `connection_url` or Redis config values specified in your `fidesops.toml`.
| `result_backend` | redis://:testpassword@redis:6379/1 | The [backend datastore](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/) where Celery will store results from asynchronously processed tasks. If not specified, fidesops will default to the `connection_url` or Redis config values specified in your `fidesops.toml`.

## Reporting a running application's configuration

You can view the currently running configuration of a fidesops application with the following request:

`GET /api/v1/config`

Please note: fidesops will filter out any sensitive configuration variables. The full list of variables deemed safe to return is:

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

For more information please see the [api docs](/fidesops/api#operations-tag-Config).
