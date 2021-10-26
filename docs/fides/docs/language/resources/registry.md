# Registry

**Demo manifest file:** `/fides/fidesctl/demo_resources/demo_registry.yml`. 


A registry is a collection of system resources. You add a system to a registry by setting the system's `registry_id` field. A system can only be long to one registry. Although a system knows which registry it belongs to, the registry doesn't know which systems it contains.

All registries are siblings: You can't create a hierarchy of registries.

Collecting your systems into registries is optional.


## Object Structure

**fides_key**<span class="required"/>_string_

A string token of your own invention that uniquely identifies this registry. It's your responsibility to ensure that the value is unique across all of your registry objects. The value may only contain `\w` characters (alphanumeric and underbar).

**name**<span class="required"/>_string_

The UI-friendly name of the registry.

**description**<span class="required"/>_string_

A human-readable description of the registry.

**organization_fides_key**<span class="spacer"/>_string_<span class="spacer"/>default: `default_organization`

The fides key of the organization to which this registry belongs.


## Examples

**YAML**
```yaml
registry:
  - fides_key: user_systems_registry
    name: User Systems Registry
    description: A registry for all of the user-related systems.
```

**JSON**
```json
{
  "fides_key": "user_systems_registry",
  "name": "User Systems Registry",
  "description": "A registry for all of the user-related systems."
}
```
