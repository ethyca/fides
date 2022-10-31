# Create Datasets

## What is a Dataset?

A _Dataset_ is the configuration you provide for a database or other queryable datastore. Fides Datasets are applicable to a wide variety of datastores beyond traditional databases. Within Datasets, the term _collection_ is used to describe an SQL table, mongo database collection, or any other single coherent set values.

## Configure a Dataset
Fides uses a YAML manifest file to represent your datastores, and requires information beyond table names and fields to fully configure a Dataset. Datastores connected in this way will be automatically traversed when Fides executes a privacy request, and will either return or update the requested data according to the associated [execution policy](./execution_policies.md).

Ensure you have created a [Connection](./database_connectors.md) for the datastore you would like to map. The Dataset defined by the following process should be [associated to the Connection](./database_connectors.md#associate-a-dataset).

### Describe a datastore 

The following is a sample database of customers and addresses. It includes a `customer` table that has a foreign key of `address_id` to an `address` table:

``` sql
CREATE TABLE CUSTOMER (
  id INT PRIMARY KEY,
  name VARCHAR,
  email VARCHAR,
  address_id int REFERENCES ADDRESS(id)
);

CREATE TABLE ADDRESS(
  id INT PRIMARY KEY,
  street VARCHAR,
  city VARCHAR,
  state VARCHAR,
  zip VARCHAR
);
```

A Fides Dataset contains a map of the database's fields, and _metadata_ describing how those fields are related. Fides uses this relationship information to navigate between different collections and fulfill privacy requests. The Dataset declaration for the above schema looks like:

``` yaml
dataset:
  - fides_key: mydatabase
    name: internal database
    description: our internal database of customer data
    collections:
      - name: address
        fields:
          - name: id
            data_categories: [system.operations]
            fidesops_meta:
              primary_key: True
          - name: street
            data_categories: [user.contact.address.street]
            fidesops_meta:
              data_type: string
          - name: city
            data_categories: [user.contact.address.city]
            fidesops_meta:
              data_type: string
          - name: state
            data_categories: [user.contact.address.state]
            fidesops_meta:
              data_type: string
          - name: zip
            data_categories: [user.contact.address.postal_code]
            fidesops_meta:
              data_type: string

      - name: customer
        after: mydatabase.address
        fields:
          - name: address_id
            data_categories: [system.operations]
            fidesops_meta:
              references:
                - dataset: mydatabase
                  field: address.id
                  direction: to
          - name: created
            data_categories: [system.operations]
          - name: email
            data_categories: [user.contact.email]
            fidesops_meta:
              identity: email
              data_type: string
          - name: id
            data_categories: [user.unique_id]
            fidesops_meta:
              primary_key: True
          - name: name
            data_categories: [user.name]
            fidesops_meta:
              data_type: string
```

#### Dataset members

| Name | Description
| --- | ----- |
| `fides_key` | A unique identifier name for the Dataset. |
| `collections` | A list of addressable collections. |
| `after` | An optional list of Datasets that must be fully traversed before this Dataset is queried. |

#### Collection members

| Name | Description
| --- | ----- |
| `name` | This collection name must correspond to the name used for it in your datastore. It will be used to dynamically generate query and update statements. |
| `fields` | A list of addressable fields in the collection. Specifying the fields in the collection tells Fides what data to address in the collection. |
| `after` | _Optional._ A list of collections (in the form `[dataset name].[collection name]`) that must be fully traversed before this collection is queried. |

#### Field members

| Name | Description
| --- | ----- |
| `name` | The name of the field will be used to generate query and update statements. **Fides does not do automated schema discovery,** and is only aware of the fields you declare.
| `data_categories` | Annotating `data_categories` connects fields to execution policy rules, and determines which actions apply to each field. For more information see [execution policies](./execution_policies.md).
| `fidesops_meta` | The `fidesops_meta` section specifies additional fields that control how Fides manages your data.
| `references` | A declaration of relationships between collections. Where the `customer` configuration declares a reference to `mydatabase:address:id`, Fides will use the values from `mydatabase.address.id` to search for related values in `customer`. References require both the Dataset and collection name to allow for multiple Dataset-collection configurations. |
| `references.field` | The linked field, using the syntax `[dataset name].[collection name ].[field name]`. |
| `references.identity` | Signifies that this field is an identity value that can be used as the root for a traversal. For more information, see [graph traversals](../guides/query_execution.md). |
| `references.direction` | *Optional.* Accepted values are `from` or `to`. This determines how fidesops uses the relationships to discover data. If the direction is `to`, fidesops will only use data in the _source_ collection to discover data in the _referenced_ collection. If the direction is `from`, fidesops will only use data in the _referenced_ collection to discover data in the _source_ collection. If the direction is omitted, fidesops will traverse the relation in whatever direction works to discover all related data.
|`references.primary_key` | *Optional.* A boolean value. Fides will treat this field as a unique row identifier for generating update statements. If no primary key is specified for any field on a collection, no updates will be generated against that collection. If multiple fields are marked as primary keys, the combination of their values will be treated as a combined key. |
| `references.data_type` | *Optional.* An indication of the type of data held by this field. Data types are used to convert values to the appropriate type when those values are used in queries. This is especially necessary when using data of one type to help locate data of another type.  Data types are also used to generate the appropriate masked value when running erasures, since fidesops needs to know the type of data expected by the field in order to generate an appropriate masked value. Available data types are `string`, `integer`, `float`, `boolean`, and `object_id`. `object` types are also supported for MongoDB.
| `references.length` | *Optional.* An indicator of field length. |
| `references.return_all_elements` | *Optional.*  For array entrypoint fields, specify whether the query should return/mask all fields, or just matching fields.  By default, we just return/mask matching fields. Setting `return_all_elements=true` will return/mask the entire array. |

### Generate a Dataset
The Fides [CLI](../cli.md) allows you to both connect to and generate a blank Dataset for your datastores. This blank Dataset does not include any annotations (e.g., Fides data descriptions) or `fidesops_meta` information, but can be used to initially map your databases.

For more information, see [generating resources](./generate_resources.md).

## Configure a manual Dataset

Not all data can be automatically retrieved. When services have no external API, or when user data is held in a physical location, you can define a Dataset to describe the types of manual fields you plan to upload, as well as any dependencies between these manual collections and other collections.

!!! Tip "When a manual Dataset is defined, an in-progress access request will pause until the data is added manually, and then resume execution. For more information, see [resuming a paused request](#resume-a-paused-access-privacy-request)."

### Describe a manual datastore

In the following example, the manual Dataset is a physical location, which contains one `storage_unit` collection. `email` is
defined as the unit's [identity](#field-members), which will then be used to retrieve the `box_id` in the storage unit.

To add a Manual Dataset, first create a [Manual Connection](./database_connectors.md#examples). The following Manual Dataset can then be [added to](database_connectors.md#associate-a-dataset) the new ConnectionConfig:

```yaml title="<code>PATCH {{host}}/connection/<manual_key>/dataset</code>"
dataset:
  - fides_key: manual_input
    name: Manual Dataset
    description: Example of a Dataset whose data must be manually retrieved
    collections:
      - name: storage_unit
        fields:
          - name: box_id
            data_categories: [ user ]
            fidesops_meta:
              primary_key: true
          - name: email
            data_categories: [ user.contact.email ]
            fidesops_meta:
              identity: email
              data_type: string
```

### Resume a paused access privacy request

A privacy request will pause execution when it reaches a manual collection in an access request.  An administrator
should manually retrieve the data and send it in a POST request.  The fields
should match the fields on the paused collection.  

Erasure requests with manual collections will also need data manually added as well.

```json title="<code>POST {{host}}/privacy-request/{{privacy_request_id}}/manual_input</code>"
[{
    "box_id": 5,
    "email": "customer-1@example.com"
}]
```

If no manual data can be found, pass in an empty list to resume the privacy request:

```json
[]
```

### Resume a paused erasure privacy request

A privacy request will pause execution when it reaches a manual collection in an erasure request.  An administrator
should manually mask the records in question, and send confirmation of the rows affected in a POST request.  

```json title="<code>POST {{host}}/privacy-request/{{privacy_request_id}}/erasure_confirm</code>"
{"row_count": 2}
```

If no manual data was destroyed, pass in a count of 0 to resume the privacy request:

```json
{"row_count": 0}
```
