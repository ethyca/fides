# Fides Resource Types

This page describes the various resources that make up the Fides platform.

## Resource Relationship Diagram

![alt text](img/Resource_Relations.svg "Fides Manifest Workflow")

## Organization

An organization is a logical grouping of resources, and all resources must belong to an organization. Fides includes a default organization with an id of 1.

=== "Example Manifest"

    ```yaml
    organization:
      fides_key: "test_organization"
      name: "Test Organization"
      description: "A test organization used to check the validity of changes."
    ```

| Name | Type | Description |
| --- | --- | --- |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String |  A name for this organization |
| description | String | A description of what this organiztion encapsulates |

---

## Privacy Classifiers

Fides uses four classifiers for describing how systems use privacy data, and for describing what privacy data can be used in what ways. All of these types support organization into hierarchical trees.

### Data Category

A Data Category describes the kind of data that is being used.

=== "Example Manifest"

    ```yaml
    data_category:
    - fides_key: "date_of_birth"
      name: "Date of Birth"
      parent_key: "user_provided_data"
      description: "User's date of birth."
    ```

=== "Example Hierarchy"

    ```yaml
    - user_provided_data
        - date_of_birth
        - job_title
    - derived data
      - sensor_data
      - user_identifiable_data
        - telemetry_data
    - account data
        - account_contact_information
        - payment_information
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Optional[Int] | Id of the organization this data category belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String |  A name for this data category |
| parent_key | Optional[String] | the fides_key of the parent category |
| description | String | A description of what this data category means or encapsulates |

### Data Use

A Data Use describes what the data is being used for.

=== "Example Manifest"

    ```yaml
    data_use:
    - fides_key: "provide_operational_support_for_contracted_service"
      name: "Provide Operational Support for Contracted Service"
      parent_key: "provide"
      description: "This usage is related to the acquisition, processing and storage of data about the usage of a cloud service (derived data) contracted by a specific cloud service customer in order to operate and protect the systems and processes necessary for the provision of this cloud service."
    ```

=== "Example Hierarchy"

    ```yaml
    - personalize
    - share
        - share_when_required_to_provide_the_service
    - promote
        - promote_based_on_contextual_information
        - promote_based_on_personalization
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Optional[Int] | Id of the organization this data use belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String | A name for this data use |
| parent_key | Optional[String] | the fides_key of the parent category |
| description | String | A description of what this data use means or encapsulates |

### Data Subject

A Data Subject describes who the data belongs to.

=== "Example Manifest"

    ```yaml
    data_subject:
    - fides_key: "anonymous_user"
      name: "Anonymous User"
      description: "A user without any identifiable information tied to them."
    ```

=== "Example Hierarchy"

    ```yaml
    - customer
    - supplier
    - job applicant
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Optional[Int] | Id of the organization this data subject belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String | A name for this data subject |
| parent_key | Optional[String] | the fides_key of the parent category |
| description | String | A description of what this data subject means or encapsulates |

### Data Qualifier

A Data Qualifier describes how private the data being used is. The hierarchy for Data Qualifiers is in order of increasing exposure.

=== "Example Manifest"

    ```yaml
    data_qualifier:
    - fides_key: "aggregated_data"
      name: "Aggregated Data"
      description: "Aggregated data is statistical data that does not contain individual-level entries and is combined from information about enough different persons that individual-level attribtures are not identifiable."
    ```

=== "Example Hierarchy"

    ```yaml
    - aggregated data
        - anonymized data
            - unlinked pseudonymized data
                - pseudonymized data
                    - identified data
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Optional[Int] | Id of the organization this data qualifier belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String | A name for this data qualifier |
| parent_key | Optional[String] | the fides_key of the parent category |
| description | String | A description of what this data qualifier means or encapsulates |

---

## Registry

A registry can optionally be used to group systems.

=== "Example Manifest"

    ```yaml
    registry:
    - organization_parent_key: 1
      fides_key: "user_systems_registry"
      name: "User Systems Registry"
      description: "A registry for all of the user-related systems."
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Int | Id of the organization this registry belongs to |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String |  A name for this registry |
| description | String | A description of what this registry means or encapsulates |

---

## System

A system represents the privacy usage of a single software project, service, codebase, or application.

=== "Example Manifest"

    ```yaml
    system:
      - organization_parent_key: 1
        registry_id: 1
        fides_key: "demoSystem"
        system_type: "service"
        meta:
          name: "Demo System"
        privacy_declarations:
          - data_categories:
              - "customer_content_data"
            data_use: "provide"
            data_qualifier: "anonymized_data"
            data_subjects:
              - "anonymous_user"
            dataset_references:
              - "user_data"
        system_dependencies: []
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Int | Id of the organization this system belongs to |
| registry_id | Optional[Int] | Id of the registry this system belongs to |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| system_type | String | The type of system being declared |
| meta | Map[String, String] | A key-value pair field to add various additional info |
| privacy_declarations | List[PrivacyDeclaration] | A list of privacy declarations (see `Privacy Declaration` below) |
| system_dependencies | List[FidesKey] | Systems that this system depends on, identified by their fides_key |

### Privacy Declaration

A Privacy Declaration describes the usage of data within a system. It is included as a composite resource within a system declaration.

| Name | Type | Description |
|  --- | --- | --- |
| data_categories | List[FidesKey] | The DataCategories for this PrivacyDeclaration |
| data_subjects | List[FidesKey] | The DataSubjects for this PrivacyDeclaration |
| data_use | List[FidesKey] | The DataUse of this PrivacyDeclaration |
| data_qualifier | List[FidesKey] | The DataQualifier for this PrivacyDeclaration |
| dataset_refereneces | List[FidesKey] | The fides_key(s) of the DatasetFields that this PrivacyDeclaration leverages. |

A Privacy Declaration can be read as "This system uses data in categories `data_categories` for `data_subjects` with the purpose of `data_use` at a qualified privacy level of `data_qualifier`"

---

## Dataset

A Dataset represents any kind of place where data is stored and includes a sub-resource that describes the fields within that dataset.

=== "Example Manifest"

    ```yaml
    dataset:
      - organization_parent_key: 1
        fides_key: "sample_db_dataset"
        name: "Sample DB Dataset"
        description: "This is a Sample Database Dataset"
        dataset_type: "MySQL"
        location: "US East" # Geographic location of the dataset
        dataset_fields:
          - name: "first_name"
            description: "A First Name Field"
            data_categories:
              - "derived_data"
            data_qualifier: "identified_data"
          - name: "email"
            description: "User's Email"
            data_categories:
              - "account_data"
            data_qualifier: "identified_data"
          - name: "Food Preference"
            description: "User's favorite food"
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Int | Id of the organization this system belongs to |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String | A name for this dataset |
| description | String | A description of what this dataset exists for |
| dataset_type | String | The type of dataset being declared |
| location | String | The physical location of the dataset |
| dataset_fields | List[DatasetField] | A list of fields (see `DatasetField` below) |

### Dataset Fields

A Dataset Field describes a single column or array of data within a dataset. Data descriptions for dataset fields do not contain data use or data subject values as those refer specifically to data usage.

| Name | Type | Description |
|  --- | --- | --- |
| name | String | A name for this field |
| description | String | A description of what this field contains |
| data_categories | List[FidesKey] | The data categories that apply to this field |
| data_qualifier | FidesKey | The data qualifier for this data |

---

## Policies

Policies group together sets of privacy rules into a single resource. These are the resources that systems and registries will be evaluated against.

=== "Example Manifest"

    ```yaml
    policy:
      organization_parent_key: 1
      fides_key: "primary_privacy_policy"
      privacy_rules:
        - fides_key: "reject_targeted_marketing"
          data_categories:
            inclusion: "ANY"
            values:
              - profiling_data
              - account_data
              - derived_data
              - cloud_service_provider_data
          data_uses:
            inclusion: ANY
            values:
              - market_advertise_or_promote
              - offer_upgrades_or_upsell
          data_subjects:
            inclusion: ANY
            values:
              - trainee
              - commuter
          data_qualifier: pseudonymized_data
          action: REJECT
        - fides_key: reject_some
          data_categories:
            inclusion: ANY
            values:
              - user_location
              - personal_health_data_and_medical_records
              - connectivity_data
              - credentials
          data_uses:
            inclusion: ALL
            values:
              - improvement_of_business_support_for_contracted_service
              - personalize
              - share_when_required_to_provide_the_service
          data_subjects:
            inclusion: NONE
            values:
              - trainee
              - commuter
              - patient
          data_qualifier: pseudonymized_data
          action: REJECT
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_parent_key | Int | Id of the organization this system belongs to |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| privacyRules | List[PrivacyRule] | see `Privacy Rule` below |

### Privacy Rule

A Privacy Rule describes a single combination of data privacy classifiers that are acceptable or not.

| Name | Type | Description |
| --- | --- | --- |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' ||
| data_categories | List[DataRule] | A list of data rules (see `Data Rule` below) |
| data_uses | List[DataRule] | A list of data rules (see `Data Rule` below) |
| data_subjects | List[DataRule] | A list of data rules (see `Data Rule` below) |
| data_qualifier | String | A data qualifier for this privacy rule |
| action | Choice | A string, either `ACCEPT` or `REJECT` |

### Data Rule

A Data Rule states what inclusion operator to use as well as a list of values to match on.

| Name | Type | Description |
| --- | --- | --- |
| inclusion | Enum | A string, either `ALL`, `NONE` or `ANY` |
| values | List[FidesKey] | A list of specific data privacy classifier fides_keys |

### Policy Rule Application

Fides uses a matching algorithm to determine whether or not each Privacy Declaration is acceptable or not. The following are some examples of how it works.

=== "Matching Rule"

    ```yaml
    # Example Privacy Rule:

    - fides_key: "rejectTargetedMarketing"
      data_categories:
        inclusion: "ANY"
        values:
          - customer_content_data
          - cloud_service_provider_data
      data_uses:
        inclusion: ANY
        values:
          - provide
          - market_advertise_or_promote
          - offer_upgrades_or_upsell
      data_subjects:
        inclusion: ANY
        values:
          - trainee
          - commuter
      data_qualifier: pseudonymized_data
      action: REJECT

    # Example Privacy Declaration:

    - data_categories:
        - "customer_content_data"
      data_uses: "provide"
      data_subjects:
        - "anonymous_user"
        - "commuter"
      data_qualifier: "psuedonymized_data"
      datasets:
        - "user_data"

    # Example Evaluation Logic:

    - Do "ANY" of the dataCategories match?
        - Yes
    - Do "ANY" of the dataUses match?
        - Yes
    - Do "NONE" of the dataSubjects match?
        - Yes
    - Is the dataQualifier at the same level of exposure or higher?
        - Yes
    - Was the answer "yes" to all of the above questions?
        - Yes
    There is a match, and the Privacy Declaration evaluates to "REJECT"!
    ```

=== "Non-Matching Rule"

    ```yaml
    # Example Privacy Rule:

    - fides_key: "rejectTargetedMarketing"
      data_categories:
        inclusion: "ANY"
        values:
          - customer_content_data
          - cloud_service_provider_data
      data_uses:
        inclusion: ANY
        values:
          - provide
          - market_advertise_or_promote
          - offer_upgrades_or_upsell
      data_subjects:
        inclusion: NONE
        values:
          - trainee
          - commuter
      data_qualifier: pseudonymized_data
      action: REJECT

    # Example Privacy Declaration:

    - data_categories:
        - "customer_content_data"
      data_uses: "provide"
      data_subjects:
        - "anonymous_user"
      data_qualifier: "anonymized_data"
      datasets:
        - "user_data"

    # Example Evaluation Logic:

    - Do "ANY" of the dataCategories match?
        - Yes
    - Do "ANY" of the dataUses match?
        - Yes
    - Do "NONE" of the dataSubjects match?
        - Yes
    - Is the dataQualifier at the same level of exposure or higher?
        - No
    - Was the answer "yes" to all of the above questions?
        - No
    There is no match!
    ```

When evaluating against a policy, Fides evaluates all privacy rules and takes the _most_ restrictive position.

---
