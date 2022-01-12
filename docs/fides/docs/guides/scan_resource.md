# Scanning a Resource

As you annotate resources with fidesctl it is important to keep your fidesctl resources up to date. The `scan` command is available to compare your resources and what is defined in your fidesctl server or resource files. It will output any part of the dataset which is not defined or categorized. The command will exit in error if a coverage threshold is not met. 

The `scan` command works best when used in tandem with the `generate-dataset` command as it creates resources in the expected format. The fidesctl format for datasets must be followed in order to be able to track coverage. 

# Scanning a Database

The `scan` command can connect to a database and compare its schema to your already defined resources. Given a database schema with a single `users` table as follows:

```shell
flaskr=# SELECT * FROM users;
 id |     created_at      |       email       |              password              | first_name | last_name
----+---------------------+-------------------+------------------------------------+------------+-----------
  1 | 2020-01-01 00:00:00 | admin@example.com | pbkdf2:sha256:260000$O87nanbSkl... | Admin      | User
  2 | 2020-01-03 00:00:00 | user@example.com  | pbkdf2:sha256:260000$PGcBy5NzZe... | Example    | User
(2 rows)
```

We have fully annotated this schema before with the following dataset resource file:
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
      data_categories: [system.operations]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: email
      description: 'Fides Generated Description for Column: email'
      data_categories: [user.provided.identifiable.contact.email]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: first_name
      description: 'Fides Generated Description for Column: first_name'
      data_categories: [user.provided.identifiable.name]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: id
      description: 'Fides Generated Description for Column: id'
      data_categories: [user.derived.identifiable.unique_id]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: last_name
      description: 'Fides Generated Description for Column: last_name'
      data_categories: [user.provided.identifiable.name]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    - name: password
      description: 'Fides Generated Description for Column: password'
      data_categories: [user.provided.identifiable.credentials.password]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

We can invoke the `scan` by simply providing a connection url for this database:
```sh
./venv/bin/fidesctl scan \
  --manifest-dir dataset.yml \
  database \
  postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/postgres
```

The command output confirms our database resource is covered fully!
```sh
Loading resource manifests from: dataset.yml
Taxonomy successfully created.
Successfully scanned the following datasets:
	public

Annotation coverage: 100%
```
