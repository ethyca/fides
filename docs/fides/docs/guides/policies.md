# Create a Fides Policy

## What is a Policy?
Fides resources provide metadata about systems and services, the data categories they process, and the uses of that data. *Policies* allow you to enforce constraints on these declarations, decide what combinations to allow or reject, and begin to control data privacy at its source.

The purpose of a privacy policy is to state what types of data are allowed for certain means of use. In Fides, a Policy is made up of rules against which the system's [resources](../getting-started/generate_resources.md) are evaluated. Policies evaluate the data subjects, data category, and data qualifier values against data use cases. This generates a boolean output to either allow or reject the process from proceeding.

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

### Sample Policy

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


## Example Policies
The following are examples of real-world use cases for Fides Policies, representing common business requirements or legislation.

!!! Note "Always ensure your Policies accurately represent your business needs prior to using them in production environments."

### No Third-Party Data Sharing

```yaml title="data_sharing_policy.yml"
policy:
  - fides_key: data_sharing_policy
    name: Data Sharing
    description: The privacy policy that governs sharing of data with third parties.
    rules:
      - name: Disallow Third-Party Marketing
        description: Disallow collecting any user contact info to use for marketing.
        data_categories:
          matches: ANY # If any of these data categories are being used
          values:
            - account
            - user
        data_uses:
          matches: ANY # And the use of the data is for third-party sharing
          values:
            - third_party_sharing
        data_subjects:
          matches: ANY # And the data subject is a customer
          values:
            - customer
        # And the data is identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

### Respecting Employee Data Privacy

```yaml title="employee_data_processing_policy.yml"
policy:
  - fides_key: employee_data_processing
    name: Employee Data Processing
    description: Restrict employee data processing only to that which is required for systematic business functions.
    rules:
      - name: Disallow Non-System Use of Employee Data
        data_categories:
          matches: ANY # If any of these data categories are being used
          values:
            - account
            - user
        data_uses:
          matches: OTHER # And the use of the data is something other than...
          values:
            - provide.service.operations
            - improve.system
            - collect
        data_subjects:
          matches: ANY # And the data subject is an employee
          values:
            - employee
        # And the data is identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

### Respecting Biometric PII

```yaml title="biometric_data_policy.yml"
policy:
  - fides_key: biometric_data_policy
    name: Biometric Data
    description: Policy that describes valid uses of biometric and health data.
    rules:
      - name: Disallow Biometrics for Profit.
        description: Disallow the use of biometric data for profit-related purposes.
        data_categories:
          matches: ANY # If any of these data categories are being used
          values:
            - user.derived
            - user.provided.identifiable.credentials.biometric_credentials
            - user.provided.identifiable.biometric
        data_uses:
          matches: ANY # And the use of the data is for any of the following...
          values:
            - advertising
            - train_ai_system
            - improve
            - third_party_sharing
        data_subjects:
          matches: ANY # And the data subject is a customer
          values:
            - customer
        # And the data is identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

### Anonymous Derived User Contact Data

```yaml title="derived_user_data_policy.yml"
policy:
  - fides_key: protect_derived_user_data
    name: Protect Derived User Data
    description: Policy that describes the proper use of derived user data.
    rules:
      - name: Disallow Non-Anonymized Derived User Data.
        description: Require that any use of derived user data must be de-identified to the anonymous level, as opposed to the pseudonymous.
        data_categories:
          matches: ANY # If any of these data categories are being used
          values:
            - user
            - account
        data_uses:
          matches: NONE # And for any data use
          values: []
        data_subjects:
          matches: ANY # And the data subject is a customer
          values:
            - customer
        # And the data is either pseudonymized or more identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized
```

### Phone Numbers for Transactional Messaging

```yaml title="transactional_messaging_policy.yaml"
policy:
  - fides_key: transactional_messaging_policy
    rules:
      - name: Transactional Messaging only for phone numbers.
        description: Allows use of phone numbers for transactional messaging only.
        data_categories:
          matches: ANY # If any of these data categories are being used
          values:
            - user.provided.identifiable.contact.phone_number
        data_uses:
          matches: OTHER # And a data use other than these have been declared
          values:
            - provide.service.operations
            - provide.service.operations.support
        data_subjects:
          matches: ANY # And the data subject is a customer
          values:
            - customer
        # And the data is identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

