# Organization

An Organization represents all or part of an enterprise or company, and establishes the root of your resource hierarchy. This means that while you can have more than one Organization resource, they can't refer to each other's sub-resources. For example, your "American Stores" Organization can't refer to the Policy objects that are defined by your "European Stores" Organization.

The Organization resource will also contain vital information with regards to compliance reporting in the case of a data map or RoPA (Record of Processing Activities).

All other resource types must refer to an Organization (through their `organization_fides_key` properties). Fides creates a default Organization that it uses for all resources that don't otherwise specify an Organization. Unless you're creating multiple Organizations (which should be rare), it is suggested to use the default Organization resource.

The fides key for the default Organization is `default_organization`.

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;_string_

A string token of your own invention that uniquely identifies this Organization. It's your responsibility to ensure that the value is unique across all of your Organization objects. The value can only contain alphanumeric characters, hyphens, periods and underscores (`[A-Za-z0-9_.-]`).

**name**<span class="required"/>&nbsp;&nbsp;_string_

A UI-friendly label for the Organization.

**description**<span class="required"/>&nbsp;&nbsp;_string_

A human-readable description of the Organization.

**controller**<span class="required"/>&nbsp;&nbsp;[array]

An array of contact information for the controller over personal data usage within the organization (`name`, `address`, `email`, `phone`).

**data_protection_officer**<span class="required"/>&nbsp;&nbsp;[array]

An array of contact information for the Data Protection Officer (DPO) within the organization (`name`, `address`, `email`, `phone`).

**representative**<span class="required"/>&nbsp;&nbsp;[array]

An array of contact information for an optional representative for the organization on behalf of the controller and/or DPO (`name`, `address`, `email`, `phone`).

**security_policy**<span class="required"/>&nbsp;&nbsp;_string_

A url to the organization security policy, (i.e. https://ethyca.com/privacy-policy/)

## Examples

### **Manifest File**

```yaml
organization:
  fides_key: default_organization
  name: Acme Incorporated
  description: An Organization that represents all of Acme Inc.
  security_policy: https://example.org/privacy
  controller:
    name: Dave L. Epper
    address: 1 Acme Pl. New York, NY
    email: controller@acmeinc.com
    phone: +1 555 555 5555
  data_protection_officer:
    name: Preet Ector
    address: 1 Acme Pl. New York, NY
    email: dpo@acmeinc.com
    phone: +1 555 555 5555
  representative:
    name: Ann Othername
    address: 1 Acme Pl. New York, NY
    email: representative@acmeinc.com
    phone: +1 555 555 5555
```

### **API Payload**

```json
{
  "fides_key": "default_organization",
  "name": "Acme Incorporated",
  "description": "An Organization that represents all of Acme Inc.",
  "security_policy": "https://example.org/privacy",
  "controller": {
    "name": "Dave L. Epper",
    "address": "1 Acme Pl. New York, NY",
    "email": "controller@acmeinc.com",
    "phone": "+1 555 555 5555"
  },
  "data_protection_officer": {
    "name": "Preet Ector",
    "address": "1 Acme Pl. New York, NY",
    "email": "dpo@acmeinc.com",
    "phone": "+1 555 555 5555"
  },
  "representative": {
    "name": "Ann Othername",
    "address": "1 Acme Pl. New York, NY",
    "email": "representative@acmeinc.com",
    "phone": "+1 555 555 5555"
  }
}
```
