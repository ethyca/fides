# Organization

A registry is a container that you can use to create groups of system resources. 


## Specification

<table class="hierarchy">
  <tr class="element">
    <td class="property">fides_key<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A string token of your own invention that uniquely identifies this registry. It's your responsibility to ensure that the value is unique across all of your registry objects.
      The value may only contain alphanumeric characters and '_'.
    </td>
  </tr>
  <tr class="element">
    <td class="property">name<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A UI-friendly name of the registry.
    </td>
  </tr>

  <tr class="element">
    <td class="property">description<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A description of the registry.
    </td>
  </tr>
    <tr class="element">
    <td class="property">organization_fides_key<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      The fides key of the organization to which this registry belongs.
    </td>
  </tr>

</table>

## Registry

A registry can optionally be used to group systems.

**Example Manifest**

```yaml
registry:
- organization_fides_key: 1
  fides_key: user_systems_registry
  name: User Systems Registry
  description: A registry for all of the user-related systems.
```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Int | Id of the organization this registry belongs to |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String |  A name for this registry |
| description | String | A description of what this registry means or encapsulates |

---

## Examples

**Demo manifest:** demo_registry.yml.

```yaml
organization:
  fides_key: default_organization
  name: Acme Incorporated
  description: An organization that represents all of Acme Inc.
```

**API Payload**
```json
{
  "fides_key": "default_organization",
  "name": "Acme Incorporated",
  "description": "An organization that represents all of Acme Inc."
}
```
