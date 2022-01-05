# Generating a Dataset

As an alternative to manually creating dataset resource files like in our [tutorial](../tutorial/dataset.md), it is possible to generate these files using the `generate-dataset` CLI command. The CLI will connect to a given resource and automatically generate a non-annotated resource YAML file in the specified location, based on the database schema. 

Not only is this the simplest way to begin annotating your resources, but it also follows the expected fidesctl format for these resources. This is important as some commands, like `scan`, expect resources to follow this format. 

# Working With a Database

The `generate-dataset` command can connect to a database and automatically generate resource YAML file. Given a database schema with a single `users` table as follows:

```shell
flaskr=# SELECT * FROM users;
 id |     created_at      |       email       |              password              | first_name | last_name
----+---------------------+-------------------+------------------------------------+------------+-----------
  1 | 2020-01-01 00:00:00 | admin@example.com | pbkdf2:sha256:260000$O87nanbSkl... | Admin      | User
  2 | 2020-01-03 00:00:00 | user@example.com  | pbkdf2:sha256:260000$PGcBy5NzZe... | Example    | User
(2 rows)
```

We can invoke the `generate-dataset` by simply providing a connection url for this database:
```sh
./venv/bin/fidesctl generate-dataset \
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
<!-- TODO: Link to the `annotate-dataset` usage documentation below, when it exists. -->
The resulting file still requires annotating the dataset with data categories to represent what is stored. 
