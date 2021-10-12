# Getting started with datasets
_In this section, we'll review what a dataset resource is, why it's needed, and how it's created and managed._

Fundamentally, your data ecosystem is built on data that is stored _somewhere_. In Fides, Datasets are used for granular, field-level annotations of exactly what data your systems are storing and where. For example, you might declare one dataset for your Postgres application database, a second dataset for your Mongo orders collection, and a third dataset for some CSV files in your storage buckets. The Dataset resource provides a database-agnostic way to annotate the fields stored in these systems with Data Categories, providing a metadata layer for other tooling to consume.

For Best Pizza Co, you can see that their 3 Datasets, `postgres appdb`, `firestore auth`, and `redshift analyticsdb` are aligned with data storage services in their data ecosystem:
![alt text](img/BestPizzaCo_DataEcosystem.png "Best Pizza Co's Data Ecosystem")

At Best Pizza Co, we'll have to create a `dataset` record for each of the 3 datasets above, starting with the first database, the Postgres Application DB. 

## Generating a Dataset Resource
First, let's retrieve the database schema of the dataset we want to annotate. Using the `generate-dataset` command, Fides will connect directly to your database only to read its schema:
```bash
root@0419219d14e1:/fides/fidesctl# fidesctl generate-dataset postgresql://USERNAME:PASSWORD@best-pizza-co.cwiy9dtqovxa.us-east-1.rds.amazonaws.com:5432/postgres dataset1.yml
Generated dataset manifest written to dataset1.yml
```
Fides has stored the structure of that database as a yaml file in the location you stored in output_filename. This file will serve as the first building block in creating Privacy as Code at the lowest level. 

```yaml
dataset:
- fides_key: appdb
    organization_fides_key: default_organization
    name: Postgres App Database
    description: 'Fides Generated Description for Dataset: Postgres App Database'
    meta: null
    data_categories: null
    data_qualifiers:
    - aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
    collections:
    - name: users
        description: 'Fides Generated Description for Table: users'
        fields:
        - name: first_name
            description: 'Fides Generated Description for Column: first_name'
            data_categories: []
            data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        - name: zip_code
            description: 'Fides Generated Description for Column: zip_code'
            data_categories: []
            data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

## Understanding the Dataset Resource
This YAML serves as the foundation of the Fides language; it answers the questions of "_What data and kinds of data do we have?_" and "_How is it organized?_". The language is built on the declaring what types of data are found in storage for your organization.

In traditional SQL, Fides defines the following:
* "datasets" as database schemas
* "collections" as database tables
* "fields" as database columns

For NoSQL datasets, Fides defines the following:
* "dataset"
* "collection" as a logical grouping of data fields (ie: in MongoDB, this is called a "Collection")
* "fields" as a reference to an individual data element grouping (ie: in MongoDB, this is called a "document")

Further, fideslang has attributes that describe what kind of data is contained in this dataset. We use the following attributes to describe the data:

| Name | Type | Description |
|  --- | --- | --- |
| name | String | The name of this field |
| description | String | A description of what this field contains |
| data_categories | List[FidesKey] | The data categories, or types of sensitive data as defined in the taxonomy, that can be found in this field |
| data_qualifier | FidesKey | Data qualifier describes the level of deidentification for the dataset |


## Create Dataset Annotations
As you can see, `fidesctl generate-dataset` has already pre-filled the required attributes for this exported YAML file. We can update the YAML file with some information that might be appropriate for your organization, such as:

```yaml
dataset:
- fides_key: appdb
  organization_fides_key: default_organization
  name: Postgres App Database
  description: 'This is our primary web application database'
  collections:
    - name: users
      description: 'Table that contains all user account data as entered by the user'
      fields:
        - name: first_name
          description: 'Fides Generated Description for Column: first_name'
          data_categories:
            - user.provided.identifiable.name
          data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        - name: zip_code
          description: 'Fides Generated Description for Column: zip_code'
          data_categories:
            - user.provided.identifiable.contact.postal_code
          data_qualifier: aggregated.anonymized.unlinked_pseudonymized
```

---
**PRO TIP**

As you're progressing with the tutorial, we recommend installing our [Fides' VS Code plugin](https://marketplace.visualstudio.com/items?itemName=fidesctl-plugin-publisher.fidesctl-config-parser), which will validate the syntax in real-time as you're writing your resource files!

---


## Maintaining a Dataset Resource
As your business grows, you will add more databases and other services where you will be storing potentially sensitive data. We recommend that updating this resource file become a part of the development process when building a new feature. 