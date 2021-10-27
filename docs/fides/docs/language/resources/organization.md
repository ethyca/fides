# Organization

**Demo manifest file:** *None*. 

An Organization represents all or part of an enterprise or company, and establishes the root of your resource hierarchy. This means that while you can have more than Organization resource, they can't refer to each other's sub-resources. For example, your "American Stores" Organization can't refer to the Policy objects that are defined by your "European Stores" Organization.

Unless you're creating multiple Organizations (which should be rare), you can ignore the Organization resource. While all of your other resources must refer to an Organization (through their `organization_fides_key` properties), Fides creates a default Organization that it uses for all resources that don't otherwise specify an Organization. 

The fides key for the default Organization is `default_organization` 

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;_string_

A string token of your own invention that uniquely identifies this Organization. It's your responsibility to ensure that the value is unique across all of your Organization objects. The value should only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). 

**name**<span class="required"/>&nbsp;&nbsp;_string_

A UI-friendly label for the Organization.

**description**<span class="required"/>&nbsp;&nbsp;_string_

A human-readable description of the Organization.



## Examples

**YAML** 
```yaml
organization:
  fides_key: default_organization
  name: Acme Incorporated
  description: An Organization that represents all of Acme Inc.
```

**JSON**
```json
{
  "fides_key": "default_organization",
  "name": "Acme Incorporated",
  "description": "An Organization that represents all of Acme Inc."
}
```
