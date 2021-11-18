## What is a Dataset?

A Fidesops _Dataset_ is the configuration you provide for a database or other queryable datastore. We use the term _Dataset_ and not _Database_ to emphasize that this will ultimately be applicable to a wide variety of datastores beyond traditional databases. With Datasets, a _Collection_ is the term used for a SQL table, mongo database collection, or any other single coherent set values.

## Configuring a Dataset

Beyond collection and field names, Fidesops needs some additional information to fully configure a Dataset. Let's look at a simple example database, and how it would be translated into a configuration in Fidesops.

#### An example database
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

A Fidesops Dataset consists of a declaration of fields, with metadata describing how those fields are related. We use the information about their relationship to navigate between different collections. The dataset declaration for the above schema looks like:

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
          - name: city
            data_categories: [user.provided.identifiable.contact.city]
          - name: state
            data_categories: [user.provided.identifiable.contact.state]
          - name: zip
            data_categories: [user.provided.identifiable.contact.postal_code]

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
          - name: id
            data_categories: [user.derived.identifiable.unique_id]
            fidesops_meta:
              primary_key: True
          - name: name
            data_categories: [user.provided.identifiable.name]
```

#### Dataset members

- `fides_key`: A unique identifier name for the dataset
- `collections`: A list of addressable collections.
- `after`: An optional list of datasets that must be fully traversed before this dataset is queried.

#### Collection members

- `name`: The name of the collection in your configuration must correspond to the name used for it in your datastore, since it will be used to generate query and update statements.
- `fields`: A list of addressable fields in the collection. Specifying the fields in the collection tells fidesOps what data to address in the collection.
- `after`: An optional list of  collections (in the form `[dataset name].[collection name]` ) that must be fully traversed before this collection is queried.

#### Field members

- `name`: The name of the field will be used to generate query and update statements. Please note that Fidesops does not do automated schema discovery. It is only aware of the fields you declare. This means that the only fields that will be addressed and retrieved by Fidesops queries are the fields you declare.
- `data_categories`: Annotating data\_categories connects fields to policy rules, and determines which actions apply to each field. For more information see [Policies](policies.md)
- `fidesops_meta`: The fidesops\_meta section specifies some additional fields that control how Fidesops manages your data:
	- `references`:  A declaration of relationships between collections. Where the configuration declares a reference to `mydatabase:address:id` it means Fidesops will use the values from `mydatabase.address.id` to search for related values in `customer`. Unlike the SQL declaration, this is not an enforceable relationship, but simply a statement of which values are connected.  In the example above, the references from the `customer` field to `mydatabase.address.id` is analogous to a SQL statement `customer id REFERENCES address.id`, with the exception that any dataset and collection can be referenced. The relationship requires you to specify the dataset as well as the collection for relationships, because you may declare a configuration with multiple datasets, where values in one collection in the first dataset are searched using values found in the second dataset.
	- `field`: The specified linked field, using the syntax `[dataset name].[collection name ].[field name]`.
	- `identity`: Signifies that this field is an identity value that can be used as the root for a traversal [See graph traversal](query_execution.md)
	- `direction`(_Optional_): Accepted values are `from` or `to`. This determines how Fidesops uses the relationships to discover data. If the direction is `to`, FidesOps will only use data in the _source_ collection to discover data in the _referenced_ collection. If the direction is `from`, Fidesops will only use data in the _referenced_ collection to discover data in the _source_ collection. If the direction is omitted, Fidesops will traverse the relation in whatever direction works to discover all related data.
	- `primary_key` (_Optional_): A boolean value that means that Fidesops will treat this field as a unique row identifier for generating update statements. If multiple fields are marked as primary keys the combination of their values will be treated as a combined key. In SQL terms, we'd issue a query that looked like `SELECT ... FROM TABLE WHERE primary_key_name_1 = value1 AND primary_key_name_2 = value2`. If no primary key is specified for any field on a collection, no updates will be generated against that collection.
	- `data_type` (_Optional_): An indication of type of data held by this field. Data types are used to convert values to the appropriate type when those values are used in queries. Data types are also used to generate the appropriate masked value when runnint erasures, since Fidesops needs to know the type of data exxpected by the field in order to generate an appropriate masked value. Available datatypes are `string`, `integer`, `float`, `boolean`, and `object_id`.
	- `length` (_Optional_): An indicator of field length.
 
