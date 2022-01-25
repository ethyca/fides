# Example Policies

This page gives a few examples of different policies one might want to use in their own organizations.

## No Third-Party Data Sharing

```yaml title="policy.yml"
policy:
  - fides_key: data_sharing_policy
    name: Data Sharing Policy
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

```yaml title="policy.yml"
policy:
  - fides_key: employee_data_processing
    name: Employee Data Processing
    description: Restrict Employee Data Processing to only what is required for systematic business functions.
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
            - provide.system
            - improve.system
        data_subjects:
          matches: ANY # And the data subject is an employee
          values:
            - employee
        # And the data is identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

## Respecting Biometric PII

```yaml title="policy.yml"
policy:
  - fides_key: biometric_data_policy
    name: Biometric Data Policy
    description: Policy that describes valid uses of biometric and health data.
    rules:
      - name: Disallow Biometrics for Profit.
        description: Disallow biometric data being used for profit-related use-cases.
        data_categories:
          matches: ANY # If any of these data categories are being used
          values:
            - user.derived.identifiable.biometric_health
            - user.provided.identifiable.biometric
        data_uses:
          matches: ANY # And the use of the data is something other than...
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

```yaml title="policy.yml"
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
            - user.derived.identifiable.biometric_health
        data_uses:
          matches: ANY # And for any data use
          values: []
        data_subjects:
          matches: ANY # And the data subject is a customer
          values:
            - customer
        # And the data is either unlinked_pseudonymized or more identifiable, trigger a violation
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized
```
