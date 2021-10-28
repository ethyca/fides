# Write a Privacy Policy (as code)

_In this section, we'll review what the Policy resource is, how to create it, and why it's used._

More than likely, there is someone in your organization that is responsible for creating privacy policies for protecting the company from a legal standpoint. *The purpose of this privacy policy is to state what types of data are allowed for certain purposes of use.*

## Understanding the policy

This policy is comprised of rules against which your system's privacy declarations are evaluated. You might be able to help your legal counsel make this, or, if you understand the legal requirements well enough, you can handle the creation yourself.

Fides' privacy declarations provide rich metadata about your systems, the data categories they process, the uses of that data, etc. Policies allow you to declare constraints on these declarations to decide what combinations to allow or reject at your company, providing a layer of automation to control data privacy at the source.

For example, you might want policies like:

* "we only allow systems that use anonymized data for product analytics purposes"
* "we do not allow systems to combine user-derived demographic and location data for marketing use"
* "we never collect biometric data"

These examples may be formal rules you follow today, or they may already be a part of your code review or privacy review practices. Fides allows us to automate the evaluation of policy rules against your privacy declarations.

Policies use the following attributes:

| Name | Type | Description |
| --- | --- | --- |
| fides_key | FidesKey | An identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and `_`. |
| data_categories | List[DataRule] | The types of sensitive data as defined by the taxonomy |
| data_uses | List[DataRule] | The various categories of data processing and operations within your organization |
| data_subjects | List[DataRule] | The individual persons to whom you data rule pertains |
| data_qualifier | String | The acceptable or non-acceptable level of deidentification |
| action | Choice | A string, either `ACCEPT` or `REJECT` |

## Writing your first policy

If you know that you cannot use identifiable contact information for direct marketing to your customers, but you can use anonymized data for analytics purposes, then you might write a policy like the following:

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
    data_qualifier: identified_data
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

As global privacy laws change and your business scales, your company's policies will evolve with them. We recommend that updating this resource file becomes a regular part of the development planning process when building a new feature.

## Next: Evaluation

In the next section, we'll put all the pieces together to see the policy execute against all of your resources, by running [Evaluations](evaluate.md).
