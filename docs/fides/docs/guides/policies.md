This page will give a few examples for different potential default policies one might want to use in their own instances.

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
          matches: ANY
          values:
            - account
            - user.derived.identifiable
            - user.provided.identifiable
        data_uses:
          matches: ANY
          values:
            - third_party_sharing
        data_subjects:
          matches: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
```

## Respect Employee Data Privacy

## Respect Biometric PII

## Anonymous Derived User Contact Data
