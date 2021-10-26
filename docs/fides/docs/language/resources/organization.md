# Organization

**Demo manifest file:** *None*. 

An organization represents all or part of an enterprise or company, and establishes the root of your resource hierarchy. This means that while you can have more than organization resource, they can't refer to each other's sub-resources. For example, your "American Stores" organization can't refer to the Policy objects that are defined by your "European Stores" organization.

Unless you're creating multiple organizations (which should be rare), you can ignore the organization resource. While all of your other resources must refer to an organization (through their `organization_fides_key` properties), Fides creates a default organization that it uses for all resources that don't otherwise specify an organization. 

The fides key for the default organization is `default_organization` 

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;_string_

A string token of your own invention that uniquely identifies this organization. It's your responsibility to ensure that the value is unique across all of your organization objects. The value may only contain `\w` characters (alphanumeric and underbar).

**name**<span class="required"/>&nbsp;&nbsp;_string_

The UI-friendly name of the organization.

**description**<span class="required"/>&nbsp;&nbsp;_string_

A human-readable description of the organization.



## Examples

**YAML** 
```yaml
organization:
  fides_key: default_organization
  name: Acme Incorporated
  description: An organization that represents all of Acme Inc.
```

**JSON**
```json
{
  "fides_key": "default_organization",
  "name": "Acme Incorporated",
  "description": "An organization that represents all of Acme Inc."
}
```
