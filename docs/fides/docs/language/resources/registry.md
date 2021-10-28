# Registry

**Demo manifest file:** `/fides/fidesctl/demo_resources/demo_registry.yml`. 


A Registry is a collection of System resources. You add a system to a Registry by setting the System's `registry_id` field. A System may belong to only one Registry. Although a System knows which Registry it belongs to, the Registry doesn't know which Systems it contains.

All Registries are siblings: You can't create a hierarchy of Registries.

Collecting your systems into Tegistries is optional. 


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
registry:
  - fides_key: user_systems_registry
    name: User Systems Registry
    description: A Registry for all of the user-related systems.
```

**API Payload**
```json
{
  "fides_key": "user_systems_registry",
  "name": "User Systems Registry",
  "description": "A Registry for all of the user-related systems."
}
```
