# System

A System is a model for describing anything that processes data for your organization (applications, services, 3rd party APIs, etc.) and describes how these datasets are used for business functions of instances of your data resources. It contains all 4 privacy attributes (`data_category`, `data_use`, `data_subject`, and `data_qualifier`).

  ```
  organization
    |-> registry (optional)
        |-> ** system **
            |-> privacy declarations
  ```

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_constrained string_

A string token of your own invention that uniquely identifies this System. It's your responsibility to ensure that the value is unique across all of your System objects. The value may only contain alphanumeric characters, underscores, and hyphens. (`[A-Za-z0-9_.-]`).

**name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A UI-friendly label for the System.

**description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the System.

**joint_controller**<span class="required"/>&nbsp;&nbsp;[array]

An optional array of contact information if a Joint Controller exists. This information can also be more granularly stored at the [dataset](/fides/language/resources/dataset/) level (`name`, `address`, `email`, `phone`).

**privacy_declarations**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[array]&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

The array of declarations describing the types of data in your system. This is a list of the privcy attributes (`data_category`, `data_use`, `data_subject`, and `data_qualifier`) for each of your systems.

**organization_fides_key**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;default: `default_organization`

The fides key of the [Organization](/fides/language/resources/organization/) to which this System belongs.

## Examples

### **Manifest File**

```yaml
system:
  - fides_key: demo_analytics_system
    name: Demo Analytics System
    description: A system used for analyzing customer behaviour.
    system_type: Service
    joint_controller:
      name: Dave L. Epper
      address: 1 Acme Pl. New York, NY
      email: controller@acmeinc.com
      phone: +1 555 555 5555
    privacy_declarations:
      - name: Analyze customer behaviour for improvements.
        data_categories:
          - user.provided.identifiable.contact
          - user.derived.identifiable.device.cookie_id
        data_use: improve.system
        data_subjects:
          - customer
        data_qualifier: identified_data
        dataset_references:
          - demo_users_dataset
```

**Demo manifest file:** `/fides/fidesctl/demo_resources/demo_system.yml`

### **API**

```json
POST /system

{
  "fides_key": "demo_analytics_system",
  "name": "Demo Analytics System",
  "description": "A system used for analyzing customer behaviour.",
  "system_type": "Service",
  "joint_controller": {
    "name": "Dave L. Epper",
    "address": "1 Acme Pl. New York, NY",
    "email": "controller@acmeinc.com",
    "phone": "+1 555 555 5555"
  },
  "privacy_declarations": [
    {
      "name": "Analyze customer behaviour for improvements.",
      "data_categories": [
        "user.provided.identifiable.contact",
        "user.derived.identifiable.device.cookie_id"
      ],
      "data_use": "improve.system",
      "data_subjects": [
        "customer"
      ],
      "data_qualifier": "identified_data",
      "dataset_references": [
        "demo_users_dataset"
      ]
    }
  ]
}
```
