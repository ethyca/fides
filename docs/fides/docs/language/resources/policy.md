# Policy

**Demo manifest file:** `/fides/fidesctl/demo_resources/demo_policy.yml`. 


A Policy is your privacy policy as code, it lists a set of acceptable and non-acceptable rules and uses all 4 privacy attributes  (`data_category`, `data_use`, `data_subject`, and `data_qualifier`). The purpose of the policy is to state what types of data are allowed for certain usages. 



## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A string token of your own invention that uniquely identifies this Policy. It's your responsibility to ensure that the value is unique across all of your Policy objects. The value may only contain alphanumeric characters and underbars (`[A-Za-z0-9_]`). 

**name**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A UI-friendly label for the Policy.

**description**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the Policy.

**data_categories**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

The [Data Categories](/fides/language/taxonomy/data_categories/) privacy attribute describes types of sensitive data as defined in the taxonomy.

**data_uses**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

The [Data Use](/fides/language/taxonomy/data_uses/) privacy attribute describes the various categories of data processing and operations at your organization.

**data_subject**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

The [Data Subjects](/fides/language/taxonomy/data_subjects/) privacy attribute describes the individual persons whose data your rule pertains to.

**data_qualifier**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

The [Data Qualifier](/fides/language/taxonomy/data_qualifiers/) privacy attribute describes the acceptable or non-acceptable level of deidentification for this data. 

**inclusion**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_enum_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

* `ANY`
* `ALL`
* `NONE`

The inclusion criteria describes how you would like this rule to be evaluated. These basic logic gates determine whether the array of privacy attributes will be fully included (`ALL`), not included at all (`NONE`), or only included if at least 1 item in the array matches (`ANY`).

**action**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_enum_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

* `ACCEPT`
* `REJECT`
* `REQUIRE`

The action describes how the policy should be enforced. These basic actions determine how the rule will be enforced. At the moment, `REJECT` is the only supported action, but ACCEPT and REQUIRE will be supported in version 1.0+.

**organization_fides_key**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;default: `default_organization`

The fides key of the [Organization](/fides/language/resources/organization/) to which this Policy belongs.


## Examples

### **Manifest File**

```yaml
policy:
  - fides_key: demo_privacy_policy
    name: Demo Privacy Policy
    description: The main privacy policy for the organization.
    rules:
      - fides_key: reject_direct_marketing
        name: Reject Direct Marketing
        description: Disallow collecting any user contact info to use for marketing.
        data_categories:
          inclusion: ANY
          values:
            - user.provided.identifiable.contact
        data_uses:
          inclusion: ANY
          values:
            - advertising
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        action: REJECT
```

### **API Payload**

```json
POST /policy
{
  "fides_key": "demo_privacy_policy",
  "organization_fides_key": "default_organization",
  "name": "string",
  "description": "The main privacy policy for the organization.",
  "rules": [
    {
      "fides_key": "reject_direct_marketing",
      "organization_fides_key": "default_organization",
      "name": "Reject Direct Marketing",
      "description": "Disallow collecting any user contact info to use for marketing.",
      "data_categories": {
        "inclusion": "ANY",
        "values": [
          "user.provided.identifiable.contact"
        ]
      },
      "data_uses": {
        "inclusion": "ANY",
        "values": [
          "advertising"
        ]
      },
      "data_subjects": {
        "inclusion": "ANY",
        "values": [
          "customer"
        ]
      },
      "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
      "action": "REJECT"
    }
  ]
}
```
