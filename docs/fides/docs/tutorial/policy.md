# Write a Policy

Fidesctl's privacy declarations provide rich metadata about systems, the data categories they process, and the uses of that data. Policies allow you to enforce constraints on these declarations and decide what combinations to allow or reject at your company, thus providing a layer of automation to control data privacy at the source.

Define a single Policy by creating a `flaskr_policy.yml` file in the `fides_resources` directory. For this project, the file should contain the following configuration:

```yml
policy:
  - fides_key: flaskr_policy
    name: Flaskr Privacy Policy
    description: A privacy policy for the example Flask app
    rules:
      - fides_key: minimize_user_identifiable_data
        name: Minimize User Identifiable Data
        description: Reject collecting any user identifiable data for uses other than system operations
        data_categories:
          inclusion: ANY
          values:
            - user.provided.identifiable
            - user.derived.identifiable
        data_uses:
          inclusion: ANY
          values:
            - improve
            - personalize
            - advertising
            - third_party_sharing
            - collect
            - train_ai_system
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        action: REJECT

      - fides_key: reject_sensitive_data
        name: Reject Sensitive Data
        description: Reject collecting sensitive user data for any use
        data_categories:
          inclusion: ANY
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
          inclusion: ANY
          values:
            - provide
            - improve
            - personalize
            - advertising
            - third_party_sharing
            - collect
            - train_ai_system
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated
        action: REJECT
```

This demo application is built without any real controls on user data, so the Fides policy is relatively restrictive. The two rules can be interpreted respectfully as:

1. Do not use identifiable data for anything other than the app's primary functions (after all, it's just a demo app!).
1. Do not collect _any_ sensitive data at all. As a safe default, this is the type of policy you might add to all projects. Later, you can make exceptions (if you are working on a project that requires these categories).

## Understanding the Policy

The purpose of a privacy policy is to state what types of data are allowed for certain means of use. In fidesctl, a Policy is comprised of rules against which the system's privacy declarations are evaluated. Policies will evaluate the data subjects, data category, and data qualifier values against data use cases. This generates a boolean output to either allow or reject the process from proceeding.

Policies use the following attributes:

| Name | Type | Description |
| --- | --- | --- |
| fides_key | FidesKey | An identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and `_`. |
| data_categories | List[DataRule] | The types of sensitive data as defined by the taxonomy |
| data_uses | List[DataRule] | The various categories of data processing and operations within your organization |
| data_subjects | List[DataRule] | The individual persons to whom you data rule pertains |
| data_qualifier | String | The acceptable or non-acceptable level of deidentification |
| action | Choice | A string, either `ACCEPT` or `REJECT` |

> For more detail on Policy resources, see the full [Policy resource documentation](../language/resources/policy.md).

### Maintaining a Policy

As global privacy laws change and businesses scale, a company's policies will evolve with them. We recommend that updating this resource file becomes a regular part of the development planning process when building a new feature.

## Check Your Progress

After making the above changes and the changes in the previous two steps, your app should resemble the state of the [`ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) at the [`fidesctl-manifests` tag](https://github.com/ethyca/fidesdemo/releases/tag/fidesctl-manifests).

## Next: Add Google Analytics

Improve usage telemetry for this project by adding the nefarious tracker, [Google Analytics](google.md).
