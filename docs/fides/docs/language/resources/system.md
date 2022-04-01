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

**system_type**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A required value to describe the type of system being modeled, examples include: Service, Application, Third Party, etc.

**data_responsibility_title**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_enum_

An attribute to describe the role of responsibility over the personal data, used when exporting to a data map.
Defaults to `Controller` if not set explicitly.

* `Controller`
* `Processor`
* `Sub-Processor`

**administrating_department**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

An optional value to identify the owning department or group of the system within your organization

**third_country_transfers**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_constrained string_

An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in [ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3)

**joint_controller**<span class="required"/>&nbsp;&nbsp;[array]

An optional array of contact information if a Joint Controller exists. This information can also be more granularly stored at the [dataset](/fides/language/resources/dataset/) level (`name`, `address`, `email`, `phone`).

**data_protection_impact_assessment**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[array]&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

The array of properties that declare the requirement for and information surrounding a Data Protection Impact Assessment (`is_required`, `progress`, `link`).

Information will be exported as part of the data map or Record of Processing Activites (RoPA)

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
    data_responsibility_title: Controller
    administrating_department: Engineering
    third_country_transfers:
    - USA
    - CAN
    joint_controller:
      name: Dave L. Epper
      address: 1 Acme Pl. New York, NY
      email: controller@acmeinc.com
      phone: +1 555 555 5555
    data_protection_impact_assessment:
      is_required: True
      progress: Complete
      link: https://example.org/analytics_system_data_protection_impact_assessment
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
  "data_responsibility_title": "Controller",
  "administrating_department": "Engineering",
  "third_country_transfers": ["USA", "CAN"],
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
