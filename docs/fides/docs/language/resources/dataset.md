# Dataset


A Dataset takes a database schema (tables and columns) and adds Fides privacy categorizations. This is a database-agnostic way to annotate privacy declarations. 

* The schema is represented as a set of "collections" (tables) that contain "fields" (columns).

* At each level -- Dataset, collection, and field, you can assign one or more Data Categories and Data Qualifiers. The Categories and Qualifiers are cascading: Those that are assigned at the Dataset level apply to all collections and fields; those at the collection level apply to the collection's fields. 

While you can create Dataset objects by hand, you typically use the `fidesctl generate-dataset`  command to create rudimentary Dataset manifest files that are based on your real-world databases. After you run the command, which creates the schema components, you add your Data Categories and Data Qualifiers to the manifest. 

You use your Datasets by adding them to Systems. A System can contain any number of Datasets, and a Dataset can be added to any number of Systems. 

Datasets cannot contain other Datasets.


## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A string token of your own invention that uniquely identifies this Dataset. It's your responsibility to ensure that the value is unique across all of your Dataset objects. The value may only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). 

**name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A UI-friendly label for the Dataset.

**description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the Dataset.

**organization_fides_key**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;default: `default_organization`

The fides key of the [Organization](/fides/language/resources/organization/) to which this Dataset belongs.

**meta**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_object_

An optional object that provides additional information about the Dataset. You can structure the object however you like. It can be a simple set of `key: value` properties or a deeply nested hierarchy of objects. How you use the object is up to you: Fides ignores it.

**data_categories**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_string_]<br/>
**data_qualifiers**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_string_]<br/>

Arrays of Data Category and Data Qualifier resources, identified by `fides_key`, that apply to all collections in the Dataset.

**collections**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_object_]<br/>

An array of objects that describe the Dataset's collections. 

**collections.name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;string<br/>

A UI-friendly label for the collection.

**collections.description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the collection.

**collections.data_categories**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_string_]<br/>
**collections.data_qualifiers**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_string_]<br/>

Arrays of Data Category and Data Qualifier resources, identified by `fides_key`, that apply to all fields in the collection.

**collections.fields**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_object_]<br/>

An array of objects that describe the collection's fields. 

**collections.fields.name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;string<br/>

A UI-friendly label for the field.

**collections.fields.description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the field.

**collections.fields.data_categories**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_string_]<br/>

Arrays of Data Categories, identified by `fides_key`, that applies to this field.

**collections.fields.data_qualifier**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_<br/>

A Data Qualifier that applies to this field. Note that this field holds a single value, therefore, the property name is singular.

## Examples

### **Manifest File**
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

### **API Payload**
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
