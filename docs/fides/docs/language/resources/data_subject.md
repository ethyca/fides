# Data Subject

**Demo manifest file:** _None_ 

A Data Subject is a label that describes a segment of  individuals whose data you store. Data Subject labels are typically fairly broad -- "Citizen", "Visitor", "Passenger", and so on -- although you can be as specific as your system needs: "Fans in Section K", for example. The Data Subject resource isn't designed to identify specific individuals.

Data Subjects are added to Policy resources through the Policy's `data_subjects` property. They aren't used by any other resource types.

Currently, Data Subjects aren't hierarchical: A Data Subject can't contain other Data Subjects. 


## Object Structure

**fides_key**<span class="required"/>_string_

A string token of your own invention that uniquely identifies this Data Subject. It's your responsibility to ensure that the value is unique across all of your Data Subject objects. The value should only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). 

**name**<span class="spacer"/>_string_

A UI-friendly label for the Data Subject. 

**description**<span class="spacer"/>_string_

A human-readable description of the Data Subject.

**organization_fides_key**<span class="spacer"/>_string_<span class="spacer"/>default: `default_organization`

The fides key of the organization to which this Data Subject belongs.


## Examples

**Manifest File**
```yaml
data_subject:
  - fides_key: supplier_vendor
    name: Supplier/Vendor
    description: An individual or organization that provides services or goods to the organization.
```

**API Payload**

```json
{
  "fides_key": "supplier_vendor",
  "name": "Supplier/Vendor",
  "description": "An individual or organization that provides services or goods to the organization"
}
```
