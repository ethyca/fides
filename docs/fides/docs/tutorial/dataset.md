# Annotate the Dataset

Making the fidesctl tools available within the app's virtual environment is just the beginning. Next, configure fidesctl for this app by annotating its resources using manifest files.

First, create a `fides_resources` directory at the project root. This is where the manifest files will be stored.

> **Note:** In a production app this directory can have any name, but it's a best practice to create a specific directory to house the fidesctl manifest files.

Fundamentally, the data ecosystem is built on data that is stored _somewhere_. In fidesctl, Datasets are used for granular, field-level annotations of exactly what data your systems are storing and where that data is stored. For example, an app might declare one dataset for a Postgres application database, a second dataset for a Mongo orders collection, and a third dataset for some CSV files in cloud storage. The Dataset resource provides a database-agnostic way to annotate the fields stored in these systems with Data Categories, providing a metadata layer consumable by other tooling.

This app contains a single PostgreSQL dataset. Create a `dataset` resource to annotate it by adding a `flaskr_postgres_dataset.yml` file to the `fides_resources` directory. To annotate this dataset correctly, go through each column of each table and answer the question: _"What data categories are stored here?"_

For this project, the file should contain the following configuration:

```yml
dataset:
- fides_key: flaskr_postgres_dataset
  name: Flaskr Example PostgreSQL Database
  description: Application database for Flaskr example app
  collections:
  - name: products
    fields:
    - name: created_at
      data_categories: [system.operations]
    - name: description
      data_categories: [user.provided.identifiable]
    - name: id
      data_categories: [system.operations]
    - name: name
      data_categories: [user.provided.identifiable]
    - name: price
      data_categories: [user.provided.identifiable]
    - name: seller_id
      data_categories: [user.derived.identifiable.unique_id]
  - name: purchases
    fields:
    - name: buyer_id
      data_categories: [user.derived.identifiable.unique_id]
    - name: city
      data_categories: [user.provided.identifiable.contact.city]
    - name: created_at
      data_categories: [system.operations]
    - name: id
      data_categories: [system.operations]
    - name: product_id
      data_categories: [system.operations]
    - name: state
      data_categories: [user.provided.identifiable.contact.state]
    - name: street_1
      data_categories: [user.provided.identifiable.contact.street]
    - name: street_2
      data_categories: [user.provided.identifiable.contact.street]
    - name: zip
      data_categories: [user.provided.identifiable.contact.postal_code]
  - name: users
    fields:
    - name: created_at
      data_categories: [system.operations]
    - name: email
      data_categories: [user.provided.identifiable.contact.email]
    - name: first_name
      data_categories: [user.provided.identifiable.name]
    - name: id
      data_categories: [user.derived.identifiable.unique_id]
    - name: last_name
      data_categories: [user.provided.identifiable.name]
    - name: password
      data_categories: [user.provided.identifiable.credentials.password]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized
```

<!-- TODO: Link to the `generate-dataset` usage documentation below, when it exists. -->

As an alternative to manually authoring the resource file, you can also use the `generate-dataset` CLI command. The CLI will connect to the database and automatically generate a non-annotated resource YAML file in the specified location, based on the database schema. For this project, the command is:

```sh
./venv/bin/fidesctl generate-dataset \
  postgresql://postgres:postgres@localhost:5432/flaskr \
  fides_resources/flaskr_postgres_dataset.yml
```

## Understanding the Dataset Resource

This YAML serves as the foundation of [`fideslang`](https://github.com/ethyca/fideslang), the Fides language; it answers "_What data and kinds of data do we have?_" and "_How is our data organized?_". The language is built on declaring the types of data found in storage for your organization.

In traditional SQL, fidesctl defines the following:

* "datasets" as database schemas
* "collections" as database tables
* "fields" as database columns

For NoSQL datasets, fidesctl defines the following:

* "dataset"
* "collection" as a logical grouping of data fields (ie: in MongoDB, this is called a "Collection")
* "fields" as a reference to an individual data element (ie: in MongoDB, this is called a "field")

Additionally, `fideslang` has attributes that describe what kind of data is contained in this dataset. We use the following attributes to describe the data:

| Name | Type | Description |
| --- | --- | --- |
| name | String | The name of this field |
| description | String | A description of what this field contains |
| data_categories | List[FidesKey] | The types of sensitive data, as defined by the taxonomy, that can be found in this field |
| data_qualifier | FidesKey | The level of deidentification for the dataset |

> For more detail on Dataset resources, see the full [Dataset resource documentation](../language/resources/dataset.md).

---

### PRO TIP

As you're progressing with the tutorial, we recommend installing our [fidesctl VS Code extension](https://marketplace.visualstudio.com/items?itemName=ethyca.fidesctl), which will validate the syntax in real-time as you're writing your resource files!

---

### Maintaining a Dataset Resource

As apps add more databases and other services to store potentially sensitive data, it is recommended that updating this resource file becomes a part of the development process when building a new feature.

## Next: Annotate the System Resource

With the underlying database resource declared, you must now include the database in an application-level [System resource annotation](system.md).
