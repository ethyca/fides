# Organization

An organization represents all or part of an enterprise or company. It establishes the root of your resource hierarchy. This means that while you can have more than organization resource, they can't refer to each other's sub-resources. For example, your "American Stores" organization can't refer to the Policy objects that are defined by your "European Stores" organization.

## Specification

<table class="hierarchy">
  <tr class="element">
    <td class="property">fides_key<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A string token of your own invention that uniquely identifies this organization. It's your responsibility to ensure that the value is unique across all of your organization objects.
      The value may only contain alphanumeric characters and '_'.
    </td>

  </tr>
    <tr class="element">
    <td class="property">name<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A UI-friendly name of the organization.
    </td>
  </tr>

  <tr class="element">
    <td class="property">description<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A description of the organization.
    </td>
  </tr>
  <tr class="element">
    <td class="property"><span class="nest"/>description<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr class="element">
    <td class="description"><span class="bump"/>
      A description of the organization.
    </td>
  </tr>
</table>


## Examples

**Demo manifest:** None. Fides automatically defines a default organization with a `fides_key` value of `organization_1`.

```yaml
organization:
  fides_key: organization_1
  name: Acme Incorporated
  description: An organization that represents all of Acme Inc.
```

**API Payload**
```json
{
  "fides_key": "organization_1",
  "name": "Acme Incorporated",
  "description": "An organization that represents all of Acme Inc."
}
```
