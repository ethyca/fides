# Registry

A Registry is a collection of System resources. You may add a System to a Registry by setting the System's `registry_id` field.

  ```
  organization
    |-> ** registry ** (optional)
        |-> system
  ```

* A System may belong to only one Registry.

* All Registries are siblings: You cannot create a hierarchy of Registries.
* Collecting your systems into Registries is optional.

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_constrained string_

A string token of your own invention that uniquely identifies this Registry. It's your responsibility to ensure that the value is unique across all of your Registry objects. The value may only contain alphanumeric characters, underscores, and hyphens. (`[A-Za-z0-9_.-]`).

**name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A UI-friendly label for the Registry.

**description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the Registry.

**organization_fides_key**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;default: `default_organization`

The fides key of the [Organization](/fides/language/resources/organization/) to which this Registry belongs.

## Examples

### **Manifest File**

```yaml
registry:
  - fides_key: user_systems_registry
    name: User Systems Registry
    description: A Registry for all of the user-related systems.
```

### **API Payload**

```json
{
  "fides_key": "user_systems_registry",
  "name": "User Systems Registry",
  "description": "A Registry for all of the user-related systems."
}
```
