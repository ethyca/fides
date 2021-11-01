# System

**Demo manifest file:** `/fides/fidesctl/demo_resources/demo_system.yml`. 


A System is a model for describing anything that processes data for your organization (applications, services, 3rd party APIs, etc.) and describes how these datasets are used for business functions of instances of your data resources. It contains all 4 privacy attributes (`data_category`, `data_use`, `data_subject`, and `data_qualifier`).




## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A string token of your own invention that uniquely identifies this System. It's your responsibility to ensure that the value is unique across all of your System objects. The value may only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). 

**name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A UI-friendly label for the Registry.

**description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the System.

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

### **API**

```json
POST /system

{
  "fides_key": "demo_analytics_system",
  "name": "Demo Analytics System",
  "description": "A system used for analyzing customer behaviour.",
  "system_type": "Service",
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
