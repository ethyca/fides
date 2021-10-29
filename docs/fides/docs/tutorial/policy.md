# Write Privacy Policy (as code)
_In this section, we'll review what the Policy resource is, how to create it and what it's used for._

More than likely, there is someone in your organization that is responsible for creating privacy policies for protecting the company from a legal standpoint. *The purpose of this privacy policy is to state what types of data are allowed for certain purposes of use.* 

## Understanding the policy
This policy is comprised of rules that your system's privacy declarations are evaluated against. You might be able to help your legal counsel make this, or you can handle the creation of this if you understand the legal requirements well enough. 

Fides' privacy declarations provide rich metadata about your systems, the data categories they process, the data uses for that data, etc. Policies allow you to declare constraints on these declarations to decide what combinations to allow or reject at your company, providing a layer of automation to control data privacy at the source.

For example, you might want policies like:

* "we only allow systems that use anonymized data for product analytics purposes"
* "we do not allow systems to combine user-derived demographic and location data for marketing use"
* "we never collect biometric data"

These are examples of "policies" that might be formal rules you follow today, or maybe they are already part of your code review or privacy review practices. Fides allows us to turn these into automated policy rules that are evaluated against your privacy declarations.


| Name | Type | Description |
| --- | --- | --- |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' ||
| data_categories | List[DataRule] | The data categories, or types of sensitive data as defined in the taxonomy |
| data_uses | List[DataRule] | Data use describes the various categories of data processing and operations at your organization |
| data_subjects | List[DataRule] | The data subjects, or individual persons whose data your rule pertains to |
| data_qualifier | String | The data qualifier describes the acceptable or non-acceptable level of deidentification |
| action | Choice | A string, either `ACCEPT` or `REJECT` |

## Writing your first policy

To put these rules to the test, for example, if you know that you cannot use identifiable contact information for directly marketing to your customers, but you can use anonymized data for analytics purposes, you might write something like this: 

```yaml
policy:
  - fides_key: main_privacy_policy
    name: Main Privacy Policy
    description: The main privacy policy for the organization.
    rules:
      - fides_key: reject_direct_marketing
        name: Reject Direct Marketing
        description: Do not allow collection or storage of any identifiable contact info to use for marketing.
        data_categories:
          inclusion: ANY
          values:
            - user.provided.identifiable.contact
        data_uses:
          inclusion: ANY
          values:
            - marketing_advertising_or_promotion
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        action: REJECT
      - fides_key: allow_anon_analytics
        name: Use only anonymized data for analytics
        description: Allow only anonymized data to be used for analytics purposes.
        data_categories:
          inclusion: ANY
          values:
            - user.provided.nonidentifiable
        data_uses:
          inclusion: ANY
          values:
            - improve_product_or_service
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized
        action: ALLOW
```

This policy will evaluate the data subjects, data category, and data qualifier values against data use cases, which generates a boolean output to either allow or reject the process from proceeding. 


## Maintaining a Policy 
As global privacy laws change and your business scales, your company's policy will evolve with them. We recommend that updating this resource file become a regular part of the development planning process when building a new feature. 

## Next: Evaluation
In the next section, we'll put all the pieces together to see the policy execute against all your resources by running [Evaluations](evaluate.md).
