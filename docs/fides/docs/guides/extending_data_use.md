# Extending Data Use


This page provides an overview of extending the [Data Use taxonomy](/fides/language/taxonomy/data_uses) for your organization. We recommend extending from the existing categories to ensure interopability inside and outside your organization.

One of the core reasons for doing this is adding attribution to be used when exporting data from Fides and adding context/clarity for legal teams to use.

If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues)

## Creating your custom Data Use

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
    parent_key: third_party_sharing.legal_obligation
  - fides_key: third_party_sharing.personalized_advertising.direct_marketing
    name: Direct Marketing
    description: Consented user information for direct marketing purposes
    recipients: 
    - Processor - marketing co. 
    legal_basis: Consent
    parent_key: third_party_sharing.personalized_advertising
```

The above example uses the existing `demo_data_use.yml` from the Fides project. Further details for each field are below:

* `fides_key`: ideally extended from the existing taxonomy using the dot (`.`) separator
* `name`: The name used here will also be surfaced as the **purpose of processing** when exporting data from Fides
* `description`: An optional description of the purpose of processing
* `recipients`: A list of recipients of personal data for this data use, our Payroll example above has multiple recipients for tax purposes
* `legal_basis`: The legal basis category for processing, used as part of exporting data from Fides
* `parent_key`: the parent Data Use fides key extended from

