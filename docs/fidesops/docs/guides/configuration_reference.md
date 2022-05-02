# Fidesops: Application Configuration Reference

In this section we'll cover:

- How to configure the Fidesops application
- Configuration variable reference
- An example `fidesops.toml` configuration file
- Reporting a running application's configuration

Take me directly to [api docs](/fidesops/api#operations-tag-Config).


## How to configure the Fidesops application

The Fidesops application configuration variables are provided in the `fidesops.toml` file in `.toml` format. Fidesops will take the first config file it finds from the following locations:

- The location according to the `FIDESOPS__CONFIG_PATH` environment variable
- The current working directory (`./fidesops.toml`)
- The parent of the current working directory (`../fidesops.toml`)
- The user's home directory (`~/fidesops.toml`)

Fidesops is also able to be run exclusively from environment variables. For more information and examples, see [Deployment](../deployment.md#step-3-setup-fidesops-web-server).


## Configuration variable reference

The `fidesops.toml` file should specify the following variables:


| TOML Variable | ENV Variable | Type | Example | Default | Description |
|---|---|---|---|---|---|
| `SERVER` | `FIDESOPS__DATABASE__SERVER` | string | postgres.internal | N/A | The networking address for the Fideops Postgres database server |
| `USER` | `FIDESOPS__DATABASE_USER` | string | postgres | N/A | The database user with which to login to the Fidesops application database |
| `PASSWORD` | `FIDESOPS__DATABASE_PASSWORD` | string | apassword | N/A | The password with which to login to the Fidesops application database |
| `PORT` | `FIDESOPS__DATABASE__PORT` | int | 5432 | 5432 | The port at which the Fidesops application database will be accessible |
| `DB` | `FIDESOPS__DATABASE_DB` | string | db | N/A | The name of the database to use in the Fidesops application database |
|---|---|---|---|---|---|
| `HOST` | `FIDESOPS__REDIS__HOST` | string | redis.internal | N/A | The networking address for the Fidesops application Redis cache |
| `PORT` | `FIDESOPS__REDIS__PORT` | int | 6379 | 6379 | The port at which the Fidesops application cache will be accessible |
| `PASSWORD` | `FIDESOPS__REDIS__PASSWORD` | string | anotherpassword | N/A | The password with which to login to the Fidesops application cache |
| `DB_INDEX` | `FIDESOPS__REDIS__DB_INDEX` | int | 0 | 0 | The Fidesops application will use this index in the Redis cache to cache data |
| `DEFAULT_TTL_SECONDS` | `FIDESOPS__REDIS__DEFAULT_TTL_SECONDS` | int | 3600 | 604800 | The number of seconds for which data will live in Redis before automatically expiring |
|---|---|---|---|---|---|
| `APP_ENCRYPTION_KEY` | `FIDESOPS__SECURITY__APP_ENCRYPTION_KEY` | string | OLMkv91j8DHiDAULnK5Lxx3kSCov30b3 | N/A | The key used to sign Fidesops API access tokens |
| `CORS_ORIGINS` | `FIDESOPS__SECURITY__CORS_ORIGINS` | List[AnyHttpUrl] | ["https://a-client.com/", "https://another-client.com"/] | N/A | A list of pre-approved addresses of clients allowed to communicate with the Fidesops application server |
| `OAUTH_ROOT_CLIENT_ID` | `FIDESOPS__SECURITY__OAUTH_ROOT_CLIENT_ID` | string | fidesopsadmin | N/A | The value used to identify the Fidesops application root API client |
| `OAUTH_ROOT_CLIENT_SECRET` | `FIDESOPS__SECURITY__OAUTH_ROOT_CLIENT_SECRET` | string | fidesopsadminsecret | N/A | The secret value used to authenticate the Fidesops application root API client |
| `OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | `FIDESOPS__SECURITY__OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | int | 1 | 11520 | The time period Fidesops API tokens will be valid |
|---|---|---|---|---|---|
|`PRIVACY_REQUEST_DELAY_TIMEOUT` | `FIDESOPS__EXECUTION__PRIVACY_REQUEST_DELAY_TIMEOUT` | int | 3600 | 3600 | The amount of time to wait for actions delaying privacy requests, for example pre and post processing webhooks.
|`TASK_RETRY_COUNT` | `FIDESOPS__EXECUTION__TASK_RETRY_COUNT` | int | 5 | 0 | The number of times a failed request will be retried
|`TASK_RETRY_DELAY` | `FIDESOPS__EXECUTION__TASK_RETRY_DELAY` | int | 20 | 1 | The delays between retries in seconds
|`TASK_RETRY_BACKOFF` | `FIDESOPS__EXECUTION__TASK_RETRY_BACKOFF` | int | 2 | 1 | The backoff factor for retries, to space out repeated retries.
|`REQUIRE_MANUAL_REQUEST_APPROVAL` | `FIDESOPS__EXECUTION__REQUIRE_MANUAL_REQUEST_APPROVAL` | bool | False | False | Whether privacy requests require explicit approval to execute
|`MASKING_STRICT` | `FIDESOPS__EXECUTION__MASKING_STRICT` | bool | True | True | If MASKING_STRICT is True, we only use "update" requests to mask data. (For third-party integrations, you should define an `update` endpoint to use.)  If MASKING_STRICT is False, you are allowing fidesops to use any defined DELETE or GDPR DELETE endpoints to remove PII. In this case, you should define `delete` or `data_protection_request` endpoints for your third-party integrations.  Note that setting MASKING_STRICT to False means that data may be deleted beyond the specific data categories that you've configured in your Policy.


## An example `fidesops.toml` configuration file

```
[database]
SERVER="db"
USER="postgres"
PASSWORD="a-password"
DB="app"
TEST_DB="test"

[redis]
HOST="redis"
PASSWORD="testpassword"
PORT=6379
CHARSET="utf8"
DEFAULT_TTL_SECONDS=3600
DB_INDEX=0

[security]
APP_ENCRYPTION_KEY="OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"
CORS_ORIGINS=["http://localhost", "http://localhost:8080"]
ENCODING="UTF-8"
OAUTH_ROOT_CLIENT_ID="fidesopsadmin"
OAUTH_ROOT_CLIENT_SECRET="fidesopsadminsecret"

[execution]
TASK_RETRY_COUNT=3
TASK_RETRY_DELAY=20
TASK_RETRY_BACKOFF=2
REQUIRE_MANUAL_REQUEST_APPROVAL=True
MASKING_STRICT=True
```

Please note: The configuration is case-sensitive, so the variables must be specified in UPPERCASE.

## Additional environment variables

 ENV Variable | Default | Description |
|---|---|---|
| `FIDESOPS__LOG_PII` | False | If this is set to "True", pii values will display unmasked in log output. This variable should always be set to "False" in production systems.
| `FIDESOPS__HOT_RELOAD` | False | If "True", the fidesops server will reload code changes without you needing to restart the server. This variable should always be set to "False" in production systems.|
| `FIDESOPS__DEV_MODE` | False | If "True", the fidesops server will log error tracebacks, and log details of third party requests. This variable should always be set to "False" in production systems.|
| `FIDESOPS__CONFIG_PATH` | None | If this variable is set to a path, that path will be used to load .toml files first. That is, any .toml files on this path will override any installed .toml files.

## - Reporting a running application's configuration

You can view the currently running configuration of a Fidesops application with the following request:

`GET /api/v1/config`

Please note: Fidesops will filter out any sensitive configuration variables. The full list of variables deemed safe to return is:

#### Postgres database

- `SERVER`
- `USER`
- `PORT`
- `DB`
- `TEST_DB`

#### Redis cache

- `HOST`
- `PORT`
- `CHARSET`
- `DECODE_RESPONSES`
- `DEFAULT_TTL_SECONDS`
- `DB_INDEX`

#### Security settings

- `CORS_ORIGINS`
- `ENCODING`
- `OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES`


#### Execution settings

- `TASK_RETRY_COUNT`
- `TASK_RETRY_DELAY`
- `TASK_RETRY_BACKOFF`
- `REQUIRE_MANUAL_REQUEST_APPROVAL`
- `MASKING_STRICT`

For more information please see the [api docs](/fidesops/api#operations-tag-Config).
