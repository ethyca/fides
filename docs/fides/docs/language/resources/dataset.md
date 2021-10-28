# Dataset


A Dataset takes a database schema (tables and columns) and adds Fides privacy categorizations.

* The schema is represented as a set of "collections" (tables) that contain "fields" (columns).

* At each level -- Dataset, collection, and field, you can assign one or more Data Categories and Data Qualifiers. The Categories and Qualifiers are cascading: Those that are assigned at the Dataset level apply to all collections and fields; those at the collection level apply to the collection's fields. 

While you can create Dataset objects by hand, you typically use the `fidesctl generate-dataset`  command to create rudimentary Dataset manifest files that are based on your real-world databases. After you run the command, which only creates the schema components, you add your Data Categories and Data Qualifiers to the manifest. 

You use your Datasets by adding them to Systems. A System can contain any number of Datasets, and a Dataset can be added to any number of Systems. 

Datasets can't contain other Datasets.


## Object Structure

**fides_key**<span class="required"/>_string_

A string token of your own invention that uniquely identifies this Registry. It's your responsibility to ensure that the value is unique across all of your Registry objects. The value may only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). 

**name**<span class="spacer"/>_string_

A UI-friendly label for the Registry.

**description**<span class="spacer"/>_string_

A human-readable description of the Registry.

**organization_fides_key**<span class="spacer"/>_string_<span class="spacer"/>default: `default_organization`

The fides key of the Organization to which this Registry belongs.

**meta**<span class="spacer"/>_object_

An optional object that provides additional information about the Dataset. You can structure the object however you like. It can be a simple set of `key: value` properties or a deeply nested hierarchy of objects. How you use the object is up to you: Fides ignores it.

**data_categories**<span class="spacer"/>[_string_]<br/>
**data_qualifiers**<span class="spacer"/>[_string_]<br/>

Arrays of Data Category and Data Qualifier resources, identified by `fides_key`, that apply to all collections in the Dataset.

**collections**<span class="spacer"/>[_object_]<br/>

An array of objects that describe the Dataset's collections. 

**collections.name**<span class="spacer"/>string<br/>

A UI-friendly label for the collection.

**collections.description**<span class="spacer"/>_string_

A human-readable description of the collection.

**collections.data_categories**<span class="spacer"/>[_string_]<br/>
**collections.data_qualifiers**<span class="spacer"/>[_string_]<br/>

Arrays of Data Category and Data Qualifier resources, identified by `fides_key`, that apply to all fields in the collection.

**collections.fields**<span class="spacer"/>[_object_]<br/>

An array of objects that describe the collection's fields. 

**collections.fields.name**<span class="spacer"/>string<br/>

A UI-friendly label for the field.

**collections.fields.description**<span class="spacer"/>_string_

A human-readable description of the field.

**collections.fields.data_categories**<span class="spacer"/>[_string_]<br/>

Arrays of Data Categories, identified by `fides_key`, that applies to this field.

**collections.fields.data_qualifier**<span class="spacer"/>_string_<br/>

A Data Qualifier that applies to this field. Since the field holds a single value of a presumably known quality, it doesn't make sense to specify more than one  Qualifier. Accordingly, the property name is singular (note well).

## Examples

**Manifest File**
```yaml
dataset:
  - fides_key: demo_users_dataset
    name: Demo Users Dataset
    description: Data collected about users for our analytics system.
    collections:
      - name: users
        description: User information
        fields:
          - name: first_name
            description: User's first name
            data_categories:
              - user.provided.identifiable.name
          - name: email
            description: User's Email
            data_categories:
              - user.provided.identifiable.contact.email
```

**API Payload**
```json
  {
    "fides_key": "demo_users_dataset",
    "name": "Demo Users Dataset",
    "description": "Data collected about users for our analytics system.",
    "collections": [
      {
        "name": "users",
        "description": "User information",
        "fields": [
          {
            "name": "first_name",
            "description": "User's first name",
            "data_categories": [
              "user.provided.identifiable.name"
            ]
          },
          {
            "name": "email",
            "description": "User's Email",
            "data_categories": [
              "user.provided.identifiable.contact.email"
            ]
          }
        ]
      }
    ]
  }
```
