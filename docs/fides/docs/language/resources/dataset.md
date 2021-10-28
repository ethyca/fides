# Dataset


A Dataset takes a database schema (tables and columns) and adds Fides categorizations of the type of data the schema is designed to contain.

* The schema is represented as a set of "collections" (tables) that contain "fields" (columns).

* At each level -- Dataset, collection, and field, you can assign one or more Data Categories and Data Qualifiers. The Categories and Qualifiers that are assigned at the Dataset level apply to all collections and fields; those at the collection level apply to the collection's fields. 

While you can create Dataset objects completely by hand, you typically use the `fidesctl generate-dataset`  command to create rudimentary Dataset manifest files that are based on your real-world databases. After you run the command, which only creates the schema components, you add your Data Categories and Data Qualifiers to the manifest. 

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


## Examples

**Manifest File**
```yaml
dataset:
  - fides_key: user_systems_dataset
    name: User Systems Registry
    description: A Registry for all of the user-related systems.
```

**API Payload**
```json
{
  "fides_key": "user_systems_dataset",
  "name": "User Systems Registry",
  "description": "A Registry for all of the user-related systems."
}
```
