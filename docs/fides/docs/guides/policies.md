# Example Policies

This page gives a few examples of different policies one might want to use in their own organizations.

## No Third-Party Data Sharing

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

## Respecting Employee Data Privacy

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
            - provide.system.operations
            - improve.system
            - collect
        data_subjects:
          matches: ANY # And the data subject is an employee
          values:
            - employee
        # And the data is identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

## Respecting Biometric PII

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

## Anonymous Derived User Contact Data

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

## Phone Numbers for Transactional Messaging

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
            - provide.system.operations
            - provide.system.operations.support
        data_subjects:
          matches: ANY # And the data subject is a customer
          values:
            - customer
        # And the data is identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```
