# Extending the Default Taxonomy


This page provides an overview of extending the Default Taxonomy for your organization. We recommend extending from the existing categories to ensure interopability inside and outside your organization.

One of the core reasons for extending a Data Use is adding attribution to be used when exporting data from Fides and adding context/clarity for legal teams.

If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues)


## Implementing a custom Data Use

The following is an example of extending the [Data Use taxonomy](/fides/language/taxonomy/data_uses).

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

The above example uses the existing `demo_data_use.yml` from the Fides project. Further details for each field are below:

* `fides_key`: Ideally extended from the existing taxonomy using the dot (`.`) separator
* `name`: The name used here will also be surfaced as the **purpose of processing** when exporting data from Fides
* `description`: An optional description of the purpose of processing
* `recipients`: A list of recipients of personal data for this data use, our Payroll example above has multiple recipients for tax purposes
* `legal_basis`: The legal basis category for processing, used as part of exporting data from Fides. Loosely tied to article 6 of the GDPR.
* `special_category`: The special cateogry associated to processing of personal data. Loosely tied to article 9 of the GDPR.
* `parent_key`: The parent Data Use fides key extended from


The new Data Use can now be referenced as part of a [privacy declaration in a system](/fides/language/resources/system)!


## Implementing a custom Data Subject

The following is an example of extending the [Data Subject taxonomy](/fides/language/taxonomy/data_subjects).

```yaml title="data_subject.yml"
data_subject:
  - fides_key: potential_customer
    name: Potential Customer
    description: A prospective individual or other organization that purchases goods or services from the organization.
    rights_available:
    - Erasure
    automated_decisions_or_profiling: true
```

The above example uses the existing `demo_data_use.yml` from the Fides project. Further details for each field are below:

* `fides_key`: Ideally extended from the existing taxonomy using the dot (`.`) separator
* `name`: The name used here will also be surfaced as the **Categories of individuals** when exporting data from Fides
* `description`: An optional description of the data subject
* `rights_available`: A list of rights available to the data subject
* `automated_decisions_or_profiling`: If automated decision-making or profiling exists for this data subject, set as true or false

The new Data Subject can now be referenced as part of a [privacy declaration in a system](/fides/language/resources/system)!
