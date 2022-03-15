# Generating Resources

As an alternative to manually creating resource files like in our [tutorial](../tutorial/dataset.md), it is possible to generate these files using the `generate` CLI command. The CLI will connect to a given resource and automatically generate a non-annotated resource YAML file in the specified location.

Once you have created your resources you will need to keep them up to date. The `scan` command is available to compare your resources and what is defined in your fidesctl server or resource files. The command will exit in error if a coverage threshold is not met. 

The `scan` and `generate` commands work best when used in tandem as they follow an expected resource format. The fidesctl format must be followed in order to be able to track coverage. 

# Working With a Database

The `generate dataset` command can connect to a database and automatically generate resource YAML file based on the database schema.

## Generating a Dataset

Given a database schema with a single `users` table as follows:

```shell
flaskr=# SELECT * FROM users;
 id |     created_at      |       email       |              password              | first_name | last_name
----+---------------------+-------------------+------------------------------------+------------+-----------
  1 | 2020-01-01 00:00:00 | admin@example.com | pbkdf2:sha256:260000$O87nanbSkl... | Admin      | User
  2 | 2020-01-03 00:00:00 | user@example.com  | pbkdf2:sha256:260000$PGcBy5NzZe... | Example    | User
(2 rows)
```

We can invoke the `generate dataset` by providing a connection url for this database:
```sh
./venv/bin/fidesctl generate dataset \
  postgresql://postgres:postgres@localhost:5432/flaskr \
  fides_resources/flaskr_postgres_dataset.yml
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

<!-- TODO: Add a section for `annotate dataset` usage below -->

## Scanning the Dataset

The `scan dataset` command can then connect to your database and compare its schema to your already defined datasets. The command output confirms our database resource is covered fully!

```sh
Loading resource manifests from: dataset.yml
Taxonomy successfully created.
Successfully scanned the following datasets:
	public

Annotation coverage: 100%
```

# Working With an AWS Account

The `generate system aws` command can connect to an AWS account and automatically generate resource YAML file based on tracked resources.

## Providing Credentials

Authentication is managed through environment variable configuration defined by [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html). 

We can define our credentials directly as environment variables:
```sh
export AWS_ACCESS_KEY_ID="<my_access_key_id>"
export AWS_SECRET_ACCESS_KEY="<my_access_key>"
export AWS_DEFAULT_REGION="us-east-1"
```

Or reference a profile through an environment variable:
```sh
export AWS_PROFILE="my_profile_1"
export AWS_DEFAULT_REGION="us-east-1"
```

## Required Permissions

The identity which is authenticated must be allowed to invoke the following actions:
* redshift:DescribeClusters
* rds:DescribeDBInstances
* rds:DescribeDBClusters

These can be supplied in an IAM policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "redshift:DescribeClusters",
                "rds:DescribeDBInstances",
                "rds:DescribeDBClusters"
            ],
            "Resource": "*"
        }
    ]
}
```

## Filtering AWS Resources

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

Any field ARN can be wildcarded by leaving it empty. 
## Generating Systems

Once credentials have been configured we can invoke the `generate system aws` command:
```sh
./venv/bin/fidesctl generate system aws \
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
## Scanning the Systems

The `scan system aws` command can then connect to your AWS account and compare its resources to your already defined systems. The command output confirms our resources are covered fully!

```sh
Loading resource manifests from: manifest.yml
Taxonomy successfully created.
Scanned 1 resource and all were found in taxonomy.
Resource coverage: 100%
```
