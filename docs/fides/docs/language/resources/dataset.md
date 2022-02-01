# Dataset

A Dataset takes a database schema (tables and columns) and adds Fides privacy categorizations. This is a database-agnostic way to annotate privacy declarations.

  ```
  organization
    |-> registry (optional)
        |-> system
            |-> ** dataset **
                |-> collections
                    |-> fields
  ```

* The schema is represented as a set of "collections" (tables) that contain "fields" (columns).

* At each level -- Dataset, collection, and field, you can assign one or more Data Categories and Data Qualifiers. The Categories and Qualifiers declared at each child level is additive, for example, if you declare a collection with category `user.derived`, and a field with category `user.provided.identifiable.name`, your dataset will contain both user-derived and user-provided name data.

While you can create Dataset objects by hand, you typically use the `fidesctl generate-dataset`  command to create rudimentary Dataset manifest files that are based on your real-world databases. After you run the command, which creates the schema components, you add your Data Categories and Data Qualifiers to the manifest.

You use your Datasets by adding them to Systems. A System can contain any number of Datasets, and a Dataset can be added to any number of Systems.

Datasets cannot contain other Datasets.

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_constrained string_

A string token of your own invention that uniquely identifies this Dataset. It's your responsibility to ensure that the value is unique across all of your Dataset objects. The value may only contain alphanumeric characters and underbars (`[A-Za-z0-9_.-]`).

**name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A UI-friendly label for the Dataset.

**description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the Dataset.

**organization_fides_key**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;default: `default_organization`

The fides key of the [Organization](/fides/language/resources/organization/) to which this Dataset belongs.

**meta**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_object_

An optional object that provides additional information about the Dataset. You can structure the object however you like. It can be a simple set of `key: value` properties or a deeply nested hierarchy of objects. How you use the object is up to you: Fides ignores it.

**joint_controller**<span class="required"/>&nbsp;&nbsp;[array]

An optional array of contact information if a Joint Controller exists. This information can also be stored at the [system](/fides/language/resources/system/) level (`name`, `address`, `email`, `phone`).

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

**collections.fields.fields**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[_object_]<br/>

An optional array of objects that describe hierarchical/nested fields (typically found in NoSQL databases)

## Examples

### **Manifest File**

```yaml
dataset:
  - fides_key: demo_users_dataset
    name: Demo Users Dataset
    description: Data collected about users for our analytics system.
    joint_controller:
      name: Dave L. Epper
      address: 1 Acme Pl. New York, NY
      email: controller@acmeinc.com
      phone: +1 555 555 5555
    collections:
      - name: users
        description: User information
        data_categories:
          - user.derived
        fields:
          - name: first_name
            description: User's first name
            data_categories:
              - user.provided.identifiable.name
          - name: email
            description: User's Email
            data_categories:
              - user.provided.identifiable.contact.email
          - name: phone
            description: User's phone numbers
            data_categories:
              - user.provided.identifiable.contact.phone_number
            fields:
              - name: mobile
                description: User's mobile phone number
                data_categories:
                  - user.provided.identifiable.contact.phone_number
              - name: home
                description: User's home phone number
                data_categories:
                  - user.provided.identifiable.contact.phone_number
```

### **API Payload**

```json
  {
    "fides_key": "demo_users_dataset",
    "name": "Demo Users Dataset",
    "description": "Data collected about users for our analytics system.",
    "joint_controller": {
      "name": "Dave L. Epper",
      "address": "1 Acme Pl. New York, NY",
      "email": "controller@acmeinc.com",
      "phone": "+1 555 555 5555"
    },
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
          },
          {
            "name": "phone",
            "description": "User's phone numbers",
            "data_categories": [
              "user.provided.identifiable.contact.phone_number"
            ],
            "fields": [
              {
                "name": "mobile",
                "description": "User's mobile phone number",
                "data_categories": [
                  "user.provided.identifiable.contact.phone_number"
                ],
              },
              {
                "name": "home",
                "description": "User's home phone number",
                "data_categories": [
                  "user.provided.identifiable.contact.phone_number"
                ]
              }
            ]
          }
        ]
      }
    ]
  }
```
