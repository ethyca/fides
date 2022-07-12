## What is a Dataset?

A fidesops _Dataset_ is the configuration you provide for a database or other queryable datastore. We use the term _Dataset_ and not database to emphasize that this will ultimately be applicable to a wide variety of datastores beyond traditional databases. With Datasets, a _collection_ is the term used for a SQL table, mongo database collection, or any other single coherent set values.

## Configure a Dataset

Beyond collection and field names, fidesops needs some additional information to fully configure a Dataset. Let's look at a simple example database, and how it would be translated into a configuration in fidesops.

### An example database
Here we have a database of customers and addresses (the example is a bit simplified from an actual SQL schema). We have a `customer` table that has a foreign key of `address_id` to an `address` table:

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

A fidesops Dataset consists of a declaration of fields, with metadata describing how those fields are related. We use the information about their relationship to navigate between different collections. The Dataset declaration for the above schema looks like:

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
            data_categories: [user.provided.identifiable.contact.street]
            fidesops_meta:
              data_type: string
          - name: city
            data_categories: [user.provided.identifiable.contact.city]
            fidesops_meta:
              data_type: string
          - name: state
            data_categories: [user.provided.identifiable.contact.state]
            fidesops_meta:
              data_type: string
          - name: zip
            data_categories: [user.provided.identifiable.contact.postal_code]
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
            data_categories: [user.provided.identifiable.contact.email]
            fidesops_meta:
              identity: email
              data_type: string
          - name: id
            data_categories: [user.derived.identifiable.unique_id]
            fidesops_meta:
              primary_key: True
          - name: name
            data_categories: [user.provided.identifiable.name]
            fidesops_meta:
              data_type: string
```

#### Dataset members

- `fides_key`: A unique identifier name for the Dataset
- `collections`: A list of addressable collections.
- `after`: An optional list of Datasets that must be fully traversed before this Dataset is queried.

#### Collection members

- `name`: The name of the collection in your configuration must correspond to the name used for it in your datastore, since it will be used to generate query and update statements.
- `fields`: A list of addressable fields in the collection. Specifying the fields in the collection tells fidesops what data to address in the collection.
- `after`: An optional list of collections (in the form `[dataset name].[collection name]` ) that must be fully traversed before this collection is queried.

#### Field members

- `name`: The name of the field will be used to generate query and update statements. Please note that fidesops does not do automated schema discovery. It is only aware of the fields you declare. This means that the only fields that will be addressed and retrieved by fidesops queries are the fields you declare.
- `data_categories`: Annotating data\_categories connects fields to policy rules, and determines which actions apply to each field. For more information see [Policies](policies.md)
- `fidesops_meta`: The fidesops\_meta section specifies some additional fields that control how fidesops manages your data:
    - `references`:  A declaration of relationships between collections. Where the configuration declares a reference to `mydatabase:address:id` it means fidesops will use the values from `mydatabase.address.id` to search for related values in `customer`. Unlike the SQL declaration, this is not an enforceable relationship, but simply a statement of which values are connected.  In the example above, the references from the `customer` field to `mydatabase.address.id` is analogous to a SQL statement `customer id REFERENCES address.id`, with the exception that any Dataset and collection can be referenced. The relationship requires you to specify the Dataset as well as the collection for relationships, because you may declare a configuration with multiple Datasets, where values in one collection in the first Dataset are searched using values found in the second Dataset.
    - `field`: The specified linked field, using the syntax `[dataset name].[collection name ].[field name]`.
    - `identity`: Signifies that this field is an identity value that can be used as the root for a traversal [See graph traversal](query_execution.md)
    - `direction`(_Optional_): Accepted values are `from` or `to`. This determines how fidesops uses the relationships to discover data. If the direction is `to`, fidesops will only use data in the _source_ collection to discover data in the _referenced_ collection. If the direction is `from`, fidesops will only use data in the _referenced_ collection to discover data in the _source_ collection. If the direction is omitted, fidesops will traverse the relation in whatever direction works to discover all related data.
    - `primary_key` (_Optional_): A boolean value that means that fidesops will treat this field as a unique row identifier for generating update statements. If no primary key is specified for any field on a collection, no updates will be generated against that collection. If multiple fields are marked as primary keys the combination of their values will be treated as a combined key. In SQL terms, we'd issue a query that looked like `SELECT ... FROM TABLE WHERE primary_key_name_1 = value1 AND primary_key_name_2 = value2`. 
    - `data_type` (_Optional_): An indication of the type of data held by this field. Data types are used to convert values to the appropriate type when those values are used in queries. This is especially necessary when using data of one type to help locate data of another type.  Data types are also used to generate the appropriate masked value when running erasures, since fidesops needs to know the type of data expected by the field in order to generate an appropriate masked value. Available data types are `string`, `integer`, `float`, `boolean`, and `object_id`. `object` types are also supported for MongoDB.
    - `length` (_Optional_): An indicator of field length.
    - `return_all_elements`: (_Optional_):  For array entrypoint fields, specify whether the query should return/mask all fields, or just matching fields.  By default, we just return/mask matching fields.  `return_all_elements=true` will return/mask the entire array.
  
## Configure a manual Dataset

Not all data can be automatically retrieved. When services have no external API, or when user data is held in a physical location, you can define a Dataset to describe the types of manual fields you plan to upload, as well as any dependencies between these manual collections and other collections. 

When a manual Dataset is defined, an in-progress access request will pause until the data is added manually, and then resume execution.

### Describe a manual Dataset

In the following example, the Manual Dataset contains one `storage_unit` collection.  `email` is 
defined as the unit's [identity](#field-members), which will then be used to retrieve the `box_id` in the storage unit.

To add a Manual Dataset, first create a [Manual ConnectionConfig](database_connectors.md#example-6-manual-connectionconfig). The following Manual Dataset can then be [added to](database_connectors.md#associate-a-dataset) the new ConnectionConfig:

```yaml title="<code>PATCH {{host}}/connection/<manual_key>/dataset</code>"
dataset:
  - fides_key: manual_input
    name: Manual Dataset
    description: Example of a Dataset whose data must be manually retrieved
    collections:
      - name: storage_unit
        fields:
          - name: box_id
            data_categories: [ user.provided ]
            fidesops_meta:
              primary_key: true
          - name: email
            data_categories: [ user.provided.identifiable.contact.email ]
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

If no manual data can be found, simply pass in an empty list to resume the privacy request:

```json
[]
```

### Resume a paused erasure privacy request

A privacy request will pause execution when it reaches a manual collection in an erasure request.  An administrator
should manually mask the records in question and send confirmation of the rows affected in a POST request.  

```json title="<code>POST {{host}}/privacy-request/{{privacy_request_id}}/erasure_confirm</code>"
{"row_count": 2}
```

If no manual data was destroyed, pass in a count of 0 to resume the privacy request:

```json
{"row_count": 0}
```