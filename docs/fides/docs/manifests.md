# Manifests

The following are example manifests for each type of object within Fides. _Note that there can only be one list of objects per type per file._

## Data Category

```yaml
data-category:
  - organizationId: 1
    fidesKey: "customer_content_data"
    name: "Customer Content Data"
    clause: "8.8.2"
    description: "Customer content data is cloud service customer data extended to include similar data objects provided to applications executing locally on the device."
```

## Data Qualifier

```yaml
data-qualifier:
  - organizationId: 1
    fidesKey: "aggregated_data"
    name: "Aggregated Data"
    clause: "8.3.6"
    description: "Aggregated data is statistical data that does not contain individual-level entries and is combined from information about enough different persons that individual-level attribtures are not identifiable."
```

## Data Subject Category

```yaml
data-subject-category:
  - organizationId: 1
    fidesKey: "anonymous_user"
    name: "Anonymous User"
    description: "A user without any identifiable information tied to them."
```

## Data Use

```yaml
data-use:
  - organizationId: 1
    fidesKey: "personalize"
    name: "Personalize"
    description: "Personalize means to use specified data categories from the source scope to change the presentation of the capabilities of the result scope or to change the selection and presentation of data or promotions, etc."
```

## Dataset

```yaml
dataset:
  - organizationId: 1
    fidesKey: "sample_db_dataset"
    name: "Sample DB Dataset"
    description: "This is a Sample Database Dataset"
    datasetType: "MySQL"
    location: "US East" # Geographic location of the dataset
    tables:
      - name: "sample_db_table_1"
        description: "Sample DB Table Description"
        fields:
          - name: "first_name"
            description: "A First Name Field"
            dataCategories:
              - "derived_data"
            dataQualifier: "identified_data"
          - name: "email"
            description: "User's Email"
            dataCategories:
              - "account_data"
            dataQualifier: "identified_data"
          - name: "Food Preference"
            description: "User's favorite food"
```

## Policy

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

## Registry

```yaml
registry:
  - organizationId: 1
    fidesKey: "test_registry"
    name: "Test Registry"
    description: "Widget Company Internal Data"
```

## System

```yaml
system:
  - organizationId: 1
    fidesOrganizationKey: "Ethyca" # The fidesKey of the Organization the system is assigned to
    registryId: 1 # The ID of the Registry that the system is assigned to
    fidesKey: "demo_system" 
    fidesSystemType: "application" # String describing the type of system
    name: "Demo System"
    description: "A system used for demos."
    declarations: # List of declarations of privacy type combinations
      - dataCategories:
          - "customer_content_data"
        dataUse: "provide"
        dataQualifier: "anonymized_data"
        dataSubjectCategories:
          - "anonymous_user"
        dataSets:
          - "UserData"
    systemDependencies: [SomeSystem] # List of fidesKeys for systems that this sytem relies on
    datasets: [UserData] # List of fidesKeys for datasets that this sytem relies on
```
