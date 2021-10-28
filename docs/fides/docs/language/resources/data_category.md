# Data Category

A Data Category denotes the meaning or purpose of a piece of data, expressed as a taxonomy. For example, the `user.provided.identifiable.job_title` Category is used for personally-identifiable job title information that was provided by the user.

Data Category objects form a tree: A Data Category can contain any number of children, but a given Category may only have one parent. You assign a child Category to a parent by setting the child's `parent_key` property. The parent Category must already exist when it's assigned (as a parent); for example, if a parent and child are declared in the same manifest file, the parent must be declared first. Because you can't refer to "undeclared parents", it's impossible to create a child->parent->child->parent->... loop.

A child Data Category knows its parent; the parent doesn't know its children. 


## Object Structure

**fides_key**<span class="required"/>_string_

A string token that uniquely identifies this Data Category. The value is a dot-separated concatenation of the `fides_key` values of the resource's ancestors plus a final element for this resource:

`grandparent.parent.this_data_category`

The final element (`this_data_category`) may only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). The dot character is reserved as a separator.


**name**<span class="spacer"/>_string_

A UI-friendly label for the Data Category. 

**description**<span class="spacer"/>_string_

A human-readable description of the Data Category.

**parent_key**<span class="spacer"/>_string_<span class="spacer"/>

The fides key of the the Data Category's parent.

**organization_fides_key**<span class="spacer"/>_string_<span class="spacer"/>default: `default_organization`

The fides key of the organization to which this Data Category belongs.


## Examples

**Manifest File**
```yaml
data_use:
  - fides_key: user.provided.identifiable.non_specific_age
    name: User Provided Non-Specific Age
    description: Age range data.
    parent_key: user.provided.identifiable
```


**API Payload**

```json
{
    "fides_key": "user.provided.identifiable.non_specific_age",
    "name": "User Provided Non-Specific Age",
    "description": "Age range data.",
    "parent_key": "user.provided.identifiable"
  }
```
