# Generate and Maintain Resources

## What is a resource?
A _resource_ is a Fides representation of a system, database, policy, or organization. Resources are maintained in YAML manifest files written in [fideslang](https://ethyca.github.io/fideslang/). Generating resources creates a template of your databases, services, or applications for further annotation and use in [privacy requests](./datasets.md) or [data maps](../guides/generate_datamaps.md).

The Fides CLI provides a `generate` command to connect to a database, and automatically generate a resource YAML file based on the database schema. The `scan` command is available to compare your existing resources against what is defined in your Fides server, or against your resource manifest files. 

The `scan` and `generate` commands work best when used in tandem, as they follow an expected resource format. The Fides format must be followed in order to be able to track coverage.

### Providing Credentials
Database credentials are provided as part of the connection string supplied. The connection string can be supplied as a command option or the fides config.

#### Command Options
A connection string can be supplied using the `connection-string` option:
```sh
...
--connection-string <my_connection_string>
...
```

The appropriate `connection-string` format for your database connector can be found in the [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/14/dialects/).

#### Fides Config
A connection string can also be defined within your Fides [configuration](../installation/configuration.md) under the `credentials` section.

```sh
[credentials]
my_database_credentials = {connection_string="<my_connection_string>"}
```

Your command can then reference the key defined in your config:
```sh
...
--credentials-id "my_database_credentials"
...
```

It is possible to use an environment variable to set credentials config values if persisting your connection string to a file is problematic. To set a connection string you can set the environment variable with a prefix of `FIDES__CREDENTIALS__` and `__` as the nested key delimiter:
```sh
export FIDES__CREDENTIALS__MY_DATABASE_CREDENTIALS__CONNECTION_STRING="<my_database_credentials>"
```

### Generating a Dataset

Given a database schema with a single `users` table as follows:

```shell
flaskr=# SELECT * FROM users;
 id |     created_at      |       email       |              password              | first_name | last_name
----+---------------------+-------------------+------------------------------------+------------+-----------
  1 | 2020-01-01 00:00:00 | admin@example.com | pbkdf2:sha256:260000$O87nanbSkl... | Admin      | User
  2 | 2020-01-03 00:00:00 | user@example.com  | pbkdf2:sha256:260000$PGcBy5NzZe... | Example    | User
(2 rows)
```

We can invoke the `generate` command by providing a connection url for this database:
```sh
./venv/bin/fides generate dataset db \
  fides_resources/flaskr_postgres_dataset.yml \
  --connection-string postgresql://postgres:postgres@localhost:5432/flaskr
```

The result is a resource file with a dataset with collections and fields to represent our schema:
```yaml
dataset:
- fides_key: public
  organization_fides_key: default_organization
  name: public
  description: 'Fides Generated Description for Schema: public'
  meta: null
  data_categories: []
  data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
  collections:
  - name: public.users
    description: 'Fides Generated Description for Table: public.users'
    data_categories: []
    data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    fields:
    - name: created_at
      description: 'Fides Generated Description for Column: created_at'
      data_categories: []
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: email
      description: 'Fides Generated Description for Column: email'
      data_categories: []
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: first_name
      description: 'Fides Generated Description for Column: first_name'
      data_categories: []
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: id
      description: 'Fides Generated Description for Column: id'
      data_categories: []
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: last_name
      description: 'Fides Generated Description for Column: last_name'
      data_categories: []
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: password
      description: 'Fides Generated Description for Column: password'
      data_categories: []
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```
The resulting file still requires annotating the dataset with data categories to represent what is stored. 

!!! Tip "**To use this Dataset in a Privacy Request,** you must add required [meta information](./datasets.md)."

<!-- TODO: Add a section for `annotate dataset` usage below -->

### Scanning the Dataset

The `scan` command can then connect to your database and compare its schema to your defined Datasets.
```sh
./venv/bin/fides scan dataset db \
  fides_resources/flaskr_postgres_dataset.yml \
  --connection-string postgresql://postgres:postgres@localhost:5432/flaskr
```

The command output confirms our database resource is covered fully:
```sh
Loading resource manifests from: dataset.yml
Taxonomy successfully created.
Successfully scanned the following datasets:
	public

Annotation coverage: 100%
```

## Working With an AWS Account
The `generate` command can connect to an AWS account and automatically generate resource YAML file based on tracked resources.

!!! Tip "Generated resources can be used as System declarations for [generating Data Maps](../guides/generate_datamaps.md)."

### Providing Credentials
AWS credentials can be provided through command options, environment variables or the fides config.

#### Command Options
Credentials can be directly supplied in your command using the `access_key_id`, `secret_access_key`, and `region` options.
```sh
...
--access_key_id "<my_access_key_id>"
--secret_access_key "<my_secret_access_key>"
--region "us-east-1"
...
```

#### Environment Variables
The simplest way to authenticate through environment variables is to set an `SECRET_ACCESS_KEY` and `ACCESS_KEY_ID`, as defined by [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables):
```sh
export AWS_ACCESS_KEY_ID="<my_access_key_id>"
export AWS_SECRET_ACCESS_KEY="<my_access_key>"
export AWS_DEFAULT_REGION="us-east-1"
```

It is also possible to reference a profile:
```sh
export AWS_PROFILE="my_profile_1"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Fides Config
Credentials can be defined within your [Fides config](../installation/configuration.md) under the credentials section.

```sh
[credentials]
my_aws_credentials = {aws_access_key_id="<my_aws_access_key_id>", aws_secret_access_key="<my_aws_secret_access_key>", region_name="us-east-1"}
```

Your command can then reference the key defined in your config.
```sh
...
--credentials-id "my_aws_credentials"
...
```

It is possible to use an environment variable to set credentials config values if persisting your keys to a config file is problematic. To set a secret access key and id, you can set the environment variable with a prefix of `FIDES__CREDENTIALS__` and `__` as the nested key delimiter:
```sh
export FIDES__CREDENTIALS__MY_AWS_CREDENTIALS__AWS_ACCESS_KEY_ID="<my_aws_access_key_id>"
export FIDES__CREDENTIALS__MY_AWS_CREDENTIALS__AWS_SECRET_ACCESS_KEY="<my_aws_secret_access_key>"
```
### Required Permissions

The identity which is authenticated must be allowed to invoke the following actions:

- redshift:DescribeClusters
- rds:DescribeDBInstances
- rds:DescribeDBClusters

#### Sample IAM Policy

These permissions can be supplied in an IAM policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "redshift:DescribeClusters",
                "rds:DescribeDBInstances",
                "rds:DescribeDBClusters",
                "tag:GetResources",
            ],
            "Resource": "*"
        }
    ]
}
```

### Filtering AWS Resources

It is possible to filter resources at the organization level by adding a resource filter within `fidesctl_meta`. The `ignore_resource_arn` filter can exclude any resources with an exact matching Amazon Resource Name (ARN) and also supports wildcards in individual ARN fields. An empty ARN field in the filter pattern works as a wildcard.

The filter can be added to the organization model within your manifest file:
```yaml
organization:
- fides_key: default_organization
  name: default_organization
  fidesctl_meta:
    resource_filters:
    - type: ignore_resource_arn
      value: 'arn:aws:rds:us-east-1:910934740016:db:database-2'
```

In the above example we explicitly ignore a single rds database but if we wanted to ignore all rds databases we could remove the partition, account id, region and database name ARN fields:
```yaml
resource_filters:
- type: ignore_resource_arn
  value: 'arn::rds:::db:'
```

Any ARN field can be wildcarded by leaving it empty.
### Generating Systems

Once credentials have been configured we can invoke the `generate system aws` command:
```sh
./venv/bin/fides generate system aws \
  fides_resources/aws_systems.yml
```

The result is a resource file with a system that represents a redshift cluster defined in our account:
```yaml
system:
- fides_key: my_redshift_cluster
  organization_fides_key: default_organization
  name: my_redshift_cluster
  description: 'Fides Generated Description for Cluster: my_redshift_cluster'
  fidesctl_meta:
    endpoint_address: my_redshift_cluster.us-east-1.redshift.amazonaws.com
    endpoint_port: '5439'
    resource_id: arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149176
  system_type: redshift_cluster
  privacy_declarations: []
```
### Scanning the Systems

The `scan` command can then connect to your AWS account and compare its resources to your already defined systems:
```sh
./venv/bin/fides scan system aws \
  fides_resources/aws_systems.yml
```

The command output confirms our resources are covered fully:
```sh
Loading resource manifests from: manifest.yml
Taxonomy successfully created.
Scanned 1 resource and all were found in taxonomy.
Resource coverage: 100%
```
## Working With an Okta Account
The `generate` command can connect to an Okta admin account and automatically generate resource YAML file based on applications your organization integrates with.

!!! Tip "Generated resources can be used as System declarations for [generating Data Maps](../guides/generate_datamaps.md)."

### Providing Credentials
Okta credentials can be provided through command options, environment variables or the Fides config.

#### Command Options
Credentials can be directly supplied in your command using the `org-url` and `token` options.
```sh
...
--token "<my_okta_client_token>"
--org-url "<my_okta_org_url>"
...
```

#### Environment Variables
The simplest way to authenticate is by using a client token, defined by the [Okta Python SDK](https://github.com/okta/okta-sdk-python#environment-variables):
```sh
export OKTA_CLIENT_TOKEN="<my_okta_client_token>"
```

It is also possible to authenticate using OAuth 2.0:
```sh
export OKTA_CLIENT_AUTHORIZATIONMODE="PrivateKey"
export OKTA_CLIENT_CLIENTID="<my_client_id>"
export OKTA_CLIENT_SCOPES="<my_scope_1,my_scope_2>"
export OKTA_CLIENT_PRIVATEKEY="<my_private_jwk>"
```

#### Fides Configuration
Credentials can be defined within your [Fides config](../installation/configuration.md) under the credentials section.

```sh
[credentials]
my_okta_credentials = {orgUrl="<my_okta_org_url>" token="<my_okta_client_token>"}
```

Your command can then reference the key defined in your config.
```sh
...
--credentials-id "my_okta_credentials"
...
```

It is possible to use an environment variable to set credentials config values if persisting your token to a file is problematic. To set a token, you can set the environment variable with a prefix of `FIDES__CREDENTIALS__` and `__` as the nested key delimiter:
```sh
export FIDES__CREDENTIALS__MY_OKTA_CREDENTIALS__TOKEN="<my_okta_client_token>"
```

### Generating Systems

Once credentials have been configured we can invoke the `generate system okta` command:
```sh
./venv/bin/fides generate system okta
  fides_resources/okta_systems.yml
```

The result is a resource file with systems that represent our application integrations:
```yaml
system:
- fides_key: 0oa4jejqcp74R9MpJ5d7
  organization_fides_key: default_organization
  name: salesforce
  description: 'Fides Generated Description for Okta Application: Salesforce.com'
  fidesctl_meta:
    resource_id: 0oa4jejqcp74R9MpJ5d7
  privacy_declarations: []
- fides_key: 0oa4jekd00tpvn5hN5d7
  organization_fides_key: default_organization
  name: google
  description: 'Fides Generated Description for Okta Application: Google Workspace'
  fidesctl_meta:
    resource_id: 0oa4jekd00tpvn5hN5d7
  privacy_declarations: []
```
### Scanning the Systems

The `scan` command can then connect to your Okta account and compare its applications to your already defined systems:
```sh
./venv/bin/fides scan system okta \
  fides_resources/okta_systems.yml
```

The command output confirms our resources are covered fully:
```sh
Loading resource manifests from: manifest.yml
Taxonomy successfully created.
Successfully scanned the following systems:
	saasure(id=0oa4h45lj1tcpqU6W5d7)
	okta_enduser(id=0oa4h45ln0xLKJnAw5d7)
	okta_browser_plugin(id=0oa4h45lnodX7MHJB5d7)
	salesforce(id=0oa4jejqcp74R9MpJ5d7)
	google(id=0oa4jekd00tpvn5hN5d7)

Resource coverage: 100%
```

## Working With a GCP Account

The `generate` command can connect to a GCP account and automatically generate resource YAML files based on tracked resources. Currently, generating datasets from BigQuery is supported.

### Providing Credentials

GCP credentials can be generated via a [service account keyfile](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating) which can be passed as a command option or the fides config. You will need to set project specific credentials for access rights, but datasets can be passed explicitly at runtime.

#### Command Options

The path to the keyfile can be directly supplied in your command using the `keyfile_path` option.
```sh
...
--keyfile-path "/path/to/keyfile.json"
...
```

#### Fides Config
Credentials can be defined within your [fides config](../installation/configuration.md) under the credentials section.

```toml
[credentials.bigquery_1]
type = "service_account"
project_id = "<my_project_id>"
private_key_id = "<my_private_key_id>"
private_key = "<my_private_key>"
client_email = "<my_client_email>"
client_id = "<my_client_id>"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "<my_cert_url>"
```

Your command can then reference the key defined in your config.
```sh
...
--credentials-id "my_gcp_credentials"
...
```

It is possible to use an environment variable to set credentials config values if persisting your keys to a config file is problematic. To set a secret access key and id, you can set the environment variable with a prefix of `FIDES__CREDENTIALS__` and `__` as the nested key delimiter:
```sh
export FIDES__CREDENTIALS__BIGQUERY_1__PRIVATE_KEY="<my_private_key>"
export FIDES__CREDENTIALS__BIGQUERY_1__CLIENT_ID="<my_client_id>"
```

### Generating a Dataset

Once credentials have been configured, the `generate dataset gcp bigquery` command can take both a configuration option and a dataset name to create the resource file.

```sh
./venv/bin/fides generate dataset gcp bigquery \
  <dataset_name> --keyfile-path ".fides/creds/bigquery.json" \
  <output_file_name>
```

The result is a resource file with a dataset that represents the bigquery dataset defined in your account.

```yaml
dataset:
- fides_key: my_bigquery_dataset
  organization_fides_key: default_organization
  name: bigquery dataset
  description: 'Fides Generated Description for Schema: BigQuery'
  data_categories: []
  data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
  retention: No retention or erasure policy
  collections:
  - name: table
    description: 'Fides Generated Description for Table: table'
    data_categories: []
    data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    fields:
    - name: column
      description: 'Fides Generated Description for Column: column'
      data_categories: []
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
...
```
