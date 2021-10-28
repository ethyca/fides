# Data Use


A Data Use is a label that denotes the way data is used in your system: "Advertising, Marketing or Promotion", "First Party Advertising", and "Sharing for Legal Obligation", as examples.

Data Use objects form a tree: A Data Use can contain any number of children, but a given Data Use may only have one parent. You assign a child Data Use to a parent by setting the child's `parent_key` property. The parent Data Use must already exist when it's assigned (as a parent); for example, if a parent and child are declared in the same manifest file, the parent must be declared first. Because you can't refer to "undeclared parents", it's impossible to create a child->parent->child->parent->... loop.

A child Data Use knows its parent; the parent doesn't know its children. 


## Object Structure

**fides_key**<span class="required"/>_string_

A string token that uniquely identifies this Data Use. The value is a dot-separated concatenation of the `fides_key` values of the resource's ancestors plus a final element for this resource:

`grandparent.parent.this_data_use`

The final element (`this_data_use`) may only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). The dot character is reserved as a separator.


**name**<span class="spacer"/>_string_

A UI-friendly label for the Data Use. 

**description**<span class="spacer"/>_string_

A human-readable description of the Data Use.

**parent_key**<span class="spacer"/>_string_<span class="spacer"/>

The fides key of the the Data Use's parent.

**organization_fides_key**<span class="spacer"/>_string_<span class="spacer"/>default: `default_organization`

The fides key of the organization to which this Data Use belongs.


## Examples

**Manifest File**
```yaml
data_use:
  - fides_key: third_party_sharing.legal_obligation
    name: Sharing for Legal Obligation
    description: Sharing of data for legal obligations, including contracts, applicable laws or regulations.
    parent_key: third_party_sharing
```


**API Payload**

```json
{
  "fides_key": "third_party_sharing.legal_obligation",
  "name": "Sharing for Legal Obligation",
  "description": "Sharing of data for legal obligations, including contracts, applicable laws or regulations.",
  "parent_key": "third_party_sharing"
}
```
