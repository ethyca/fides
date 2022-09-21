# Extending the Default Taxonomy

Fides' default taxonomy can be extended to ensure interoperability inside and outside your organization. Extending the existing categories allows the use of attribution when exporting data from Fides, and when adding context or clarity for legal teams.


If you have suggestions for core categories that should ship with the taxonomy, requests can be submitted on the [Fides Github](https://github.com/ethyca/fides/issues).


## Implementing a custom Data Use

 A Data Use is a label that denotes the way data is used in your system. The following is an example of extending the default [Data Use taxonomy](https://ethyca.github.io/fideslang/taxonomy/data_uses/):

```yaml title="data_use.yml"
data_use:
  - fides_key: third_party_sharing.legal_obligation.payroll
    name: Payroll
    description: Legally obliged sharing of payroll information
    recipients:
    - HMRC
    - IRS
    - NYDTF
    legal_basis: Legal Obligation
    special_category: Employment
    parent_key: third_party_sharing.legal_obligation
  - fides_key: third_party_sharing.personalized_advertising.direct_marketing
    name: Direct Marketing
    description: Consented user information for direct marketing purposes
    recipients:
    - Processor - marketing co.
    legal_basis: Consent
    special_category: Consent
    parent_key: third_party_sharing.personalized_advertising
```

The above example uses the existing `demo_data_uses.yml` from the [Fides project](https://github.com/ethyca/fides). Further details for each field are below:

| Field | Description |
|----|------|
|`fides_key` | Ideally extended from the existing taxonomy using the dot (`.`) separator. A string token that uniquely identifies this Data Use. |
| `name`     | A UI-friendly name that will also be surfaced as the **Purpose of Processing** when exporting data from Fides. |
| `description` | An optional description of the purpose of processing. |
| `recipients` |A list of recipients of personal data for this data use. The Payroll example above has multiple recipients for tax purposes. |
| `legal_basis` | The legal basis category for processing, used as part of exporting data from Fides. Loosely tied to article 6 of the GDPR. |
| `special_category` | The special category associated to processing of personal data. Loosely tied to article 9 of the GDPR. |
| `parent_key` | The parent Data Use `fides_key` extended from. |



## Implementing a custom Data Subject
A Data Subject is a label that describes a segment of individuals whose data you store. The following is an example of extending the [Data Subject taxonomy](https://ethyca.github.io/fideslang/taxonomy/data_subjects/):

```yaml title="data_subject.yml"
data_subject:
  - fides_key: potential_customer
    name: Potential Customer
    description: A prospective individual or other organization that purchases goods or services from the organization.
    rights:
      strategy: INCLUDE
      values:
      - Informed
      - Access
      - Rectification
      - Erasure
      - Object
    automated_decisions_or_profiling: true
```
The above example uses the existing `demo_data_subjects.yml` from the [Fides project](https://github.com/ethyca/fides). Further details for each field are below:

| Label | Description |
|----|------|
| `fides_key` | Ideally extended from the existing taxonomy using the dot (`.`) separator. A string token that uniquely identifies this Data Use. |
| `name` | A UI-friendly name that will also be surfaced as the **Categories of individuals**  when exporting data from Fides. |
| `description` | An optional description of the data subject. |
| `rights` | A strategy of how to apply data subject rights, along with an optional list to complement the strategy. |
| `automated_decisions_or_profiling` | If automated decision-making or profiling exists for this data subject, set as either true or false. |

## Next Steps
Once created, your new Data Subject or Data Use can be referenced as part of a [privacy declaration in a system](https://ethyca.github.io/fideslang/resources/system), throughout your [policies](https://ethyca.github.io/fideslang/resources/policy), and in other Fides [resources](https://ethyca.github.io/fideslang/resources/dataset).