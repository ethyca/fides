# Fides Documentation

Fides is a data privacy tool that lives within the `Software Development Life Cycle`. It is designed to help companies stay compliant by briding the gap between compliance officers and engineers. By describing the flow of data within systems as Fides manifests, Fides is able to continually check for compliance and warn users of potentially unsafe changes before they make it into production.

When data governance is documented in the source code by engineers, it makes it possible for organizations to handle data privacy in a proactive manner, instead of a reactive one.

## Principles

* Data Lineage as YAML
* Compliance controls at the CI layer
* Synergy between engineers and lawyers

## Example

To make things more concrete, the following is a realistic example of how Fides supports proactive compliance with data privacy laws.

An engineer is using a system with the following manifest:

```yaml
system:
  - organizationId: 1
    fidesOrganizationKey: "Ethyca"
    registryId: 1
    fidesKey: "demoSystem"
    fidesSystemType: "SYSTEM"
    name: "Demo System"
    description: "A system used for demos."
    declarations:
      - dataCategories:
          - "customer_content_data"
        dataUse: "provide"
        dataQualifier: "anonymized_data"
        dataSubjectCategories:
          - "anonymous_user"
        dataSets:
          - "user_data"
    systemDependencies: []
    datasets: ["user_data"]
```

and the following policy:

```yaml
policy:
  organizationId: 1
  fidesKey: "primaryPrivacyPolicy"
  rules:
    - organizationId: 1
      fidesKey: "rejectTargetedMarketing"
      dataCategories:
        inclusion: "ANY"
        values:
          - profiling_data
          - account_data
          - derived_data
          - cloud_service_provider_data
      dataUses:
        inclusion: ANY
        values:
          - market_advertise_or_promote
          - offer_upgrades_or_upsell
      dataSubjectCategories:
        inclusion: ANY
        values:
          - trainee
          - commuter
      dataQualifier: pseudonymized_data
      action: REJECT
    - organizationId: 1
      fidesKey: rejectSome
      dataCategories:
        inclusion: ANY
        values:
          - user_location
          - personal_health_data_and_medical_records
          - connectivity_data
          - credentials
      dataUses:
        inclusion: ALL
        values:
          - improvement_of_business_support_for_contracted_service
          - personalize
          - share_when_required_to_provide_the_service
      dataSubjectCategories:
        inclusion: NONE
        values:
          - trainee
          - commuter
          - patient
      dataQualifier: pseudonymized_data
      action: REJECT
```

With this current configuration, everything passes and all policies are being respected. However, the engineer is going to add a new feature that will require the system manifest to be updated. The new manifest looks like this:

```yaml
system:
  - organizationId: 1
    fidesOrganizationKey: "Ethyca"
    registryId: 1
    fidesKey: "demoSystem"
    fidesSystemType: "SYSTEM"
    name: "Demo System"
    description: "A system used for demos."
    declarations:
      - dataCategories:
          - "customer_content_data"
        dataUse: "provide"
        dataQualifier: "anonymized_data"
        dataSubjectCategories:
          - "anonymous_user"
        dataSets:
          - "user_data"
      - dataCategories:
          - "connectivity_data"
        dataUse: "personalize"
        dataQualifier: "identified_data"
        dataSubjectCategories:
          - "user"
        dataSets:
          - "user_data"
    systemDependencies: []
    datasets: ["user_data"]
```

There is now a second data declaration within the system manifest, and it shows that identifiable user data is being used to personalize the user experience. Our policy defines that this is an illegal combination of categories and qualifiers, so this will fail its evaluation with the Fides server.

The next step is to reach out to compliance and collaborate on the technical needs of the feature, and how they can be potentially updated to fit within the confines of the existing privacy policies.

After discussing with the compliance team, it is decided that the feature can be tweaked to comply with privacy laws while still adding value for the user, which is reflected in the following system manifest:

```yaml
system:
  - organizationId: 1
    fidesOrganizationKey: "Ethyca"
    registryId: 1
    fidesKey: "demoSystem"
    fidesSystemType: "SYSTEM"
    name: "Demo System"
    description: "A system used for demos."
    declarations:
      - dataCategories:
          - "customer_content_data"
        dataUse: "provide"
        dataQualifier: "anonymized_data"
        dataSubjectCategories:
          - "anonymous_user"
        dataSets:
          - "user_data"
      - dataCategories:
          - "connectivity_data"
        dataUse: "personalize"
        dataQualifier: "anonymized_data"
        dataSubjectCategories:
          - "user"
        dataSets:
          - "user_data"
    systemDependencies: []
    datasets: ["user_data"]
```

The dataQualifier for the new feature is now `anonymized_data` instead of `pseudonymized_data`, which complies with data privacy laws for this use and categories.

For further info on how to use and configure Fides, visit the [Getting Started](getting_started.md) page.
