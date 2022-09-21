# Create a Fides Policy

## What is a Policy?
Fides resources provide metadata about systems and services, the data categories they process, and the uses of that data. *Policies* allow you to enforce constraints on these declarations, decide what combinations to allow or reject, and begin to control data privacy at its source.

The purpose of a privacy policy is to state what types of data are allowed for certain means of use. In Fides, a Policy is made up of rules against which the system's [resources](./generate_resources.md) are evaluated. Policies evaluate the data subjects, data category, and data qualifier values against data use cases. This generates a boolean output to either allow or reject the process from proceeding.

### Policy attributes
Policies use the following attributes:

| Name | Type | Description |
| --- | --- | --- |
| `fides_key` | FidesKey | An identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and `_`. |
| `data_categories` | List[DataRule] | The types of sensitive data as defined by the taxonomy. |
| `data_uses` | List[DataRule] | The various categories of data processing and operations within your organization. |
| `data_subjects` | List[DataRule] | The individual persons to whom you data rule pertains. |
| `data_qualifier` | String | The acceptable or non-acceptable level of de-identification. |

!!! Tip "For more detail on Policy resources, see the full [Policy resource documentation](https://ethyca.github.io/fideslang/resources/policy)."

### Example Policy

```yaml
policy:
  - fides_key: flaskr_policy
    name: Flaskr Privacy Policy
    description: A privacy policy for the example Flask app
    rules:
      - fides_key: minimize_user_identifiable_data
        name: Minimize User Identifiable Data
        description: Reject collecting any user identifiable data for uses other than system operations
        data_categories:
          matches: ANY
          values:
            - user.provided.identifiable
            - user.derived.identifiable
        data_uses:
          matches: ANY
          values:
            - improve
            - personalize
            - advertising
            - third_party_sharing
            - collect
            - train_ai_system
        data_subjects:
          matches: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified

      - fides_key: reject_sensitive_data
        name: Reject Sensitive Data
        description: Reject collecting sensitive user data for any use
        data_categories:
          matches: ANY
          values:
            - user.provided.identifiable.biometric
            - user.provided.identifiable.childrens
            - user.provided.identifiable.genetic
            - user.provided.identifiable.health_and_medical
            - user.provided.identifiable.political_opinion
            - user.provided.identifiable.race
            - user.provided.identifiable.religious_belief
            - user.provided.identifiable.sexual_orientation
        data_uses:
          matches: ANY
          values:
            - provide
            - improve
            - personalize
            - advertising
            - third_party_sharing
            - collect
            - train_ai_system
        data_subjects:
          matches: ANY
          values:
            - customer
        data_qualifier: aggregated
```

This Fides policy is relatively restrictive. The two rules (`minimize_user_identifiable_data` and `reject_sensitive_data`) can be interpreted as:

1. Do not use identifiable data for anything other than the app's primary functions.
1. Do not collect _any_ sensitive data at all. As a safe default, this is the type of policy you might add to all projects.


## Maintaining your Policies
As global privacy laws change and businesses scale, a company's policies will evolve with them. Updating this resource file should become a regular part of the development planning process when building a new feature. 

For more use cases, Fides provides several [sample Policies](./policies.md) for use in real-world regulation scenarios.
