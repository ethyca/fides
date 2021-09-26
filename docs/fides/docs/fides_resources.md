# Fides Resource Types

This page describes the various resources that make up the Fides platform.

## Resource Relationship Diagram

![alt text](img/Resource_Relations.svg "Fides Manifest Workflow")

## Organization

An organization is a logical grouping of resources, and all resources must belong to an organization. Fides includes a default organization with an id of 1.

=== Example Manifest

    ```yaml
    organization:
      fides_key: test_organization
      name: Test Organization
      description: A test organization used to check the validity of changes.
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

=== Example Manifest

    ```yaml
    data_category:
    - fides_key: user.provided.identifiable.date_of_birth
      name: Date of Birth
      parent_key: user.provided.identifiable
      description: User's date of birth.
    ```

=== Example Hierarchy

    ```yaml
    - user
      - user.provided
        - user.provided.identifiable
          - user.provided.identifiable.date_of_birth
          - user.provided.identifiable.job_title
        user.provided.nonidentifiable
      - user.derived
        - user.derived.identifiable
        - user.derived.nonidentifiable
    - account
        - account.contact
        - account.payment
    - system
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Optional[Int] | Id of the organization this data category belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String |  A name for this data category |
| parent_key | Optional[FidesKey] | the fides_key of the parent category |
| description | String | A description of what this data category means or encapsulates |

### Data Use

A Data Use describes what the data is being used for.

=== Example Manifest

    ```yaml
    data_use:
    - fides_key: provide_product_or_service.support
      name: Support the Product or Service
      parent_key: provide_product_or_service
    ```

=== Example Hierarchy

    ```yaml
    - provide_product_or_service
      - provide_product_or_service.support
      - provide_product_or_service.support_optimization
      - provide_product_or_service.offer_upgrades
    - third_party_sharing
      - third_party_sharing.payment_processing
      - third_party_sharing.personalized_advertising
      - third_party_sharing.legal_obligation
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Optional[Int] | Id of the organization this data use belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String | A name for this data use |
| parent_key | Optional[FidesKey] | the fides_key of the parent category |
| description | String | A description of what this data use means or encapsulates |

### Data Subject

A Data Subject describes who the data belongs to.

=== Example Manifest

    ```yaml
    data_subject:
    - fides_key: anonymous_user
      name: Anonymous User
      description: A user without any identifiable information tied to them.
    ```

=== Example Hierarchy

    ```yaml
    - customer
    - supplier
    - employee
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Optional[Int] | Id of the organization this data subject belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String | A name for this data subject |
| description | String | A description of what this data subject means or encapsulates |

### Data Qualifier

A Data Qualifier describes how private the data being used is. The hierarchy for Data Qualifiers is in order of increasing exposure.

=== Example Manifest

    ```yaml
    data_qualifier:
    - fides_key: aggregated_data
      name: Aggregated Data
      description: Aggregated data is statistical data that does not contain individual-level entries and is combined from information about enough different persons that individual-level attribtures are not identifiable.
    ```

=== Example Hierarchy

    ```yaml
    - aggregated data
        - anonymized data
            - unlinked pseudonymized data
                - pseudonymized data
                    - identified data
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Optional[Int] | Id of the organization this data qualifier belongs to, defaults to 1 |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String | A name for this data qualifier |
| description | String | A description of what this data qualifier means or encapsulates |

---

## Registry

A registry can optionally be used to group systems.

=== Example Manifest

    ```yaml
    registry:
    - organization_fides_key: 1
      fides_key: user_systems_registry
      name: User Systems Registry
      description: A registry for all of the user-related systems.
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Int | Id of the organization this registry belongs to |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| name | String |  A name for this registry |
| description | String | A description of what this registry means or encapsulates |

---

## System

A system represents the privacy usage of a single software project, service, codebase, or application.

=== Example Manifest

    ```yaml
    system:
      - organization_fides_key: 1
        fides_key: demo_analytics_system
        name: Demo Analytics System
        description: A system used for analyzing customer behaviour.
        system_type: Service
        privacy_declarations:
          - name: Analyze customer behaviour for improvements.
            data_categories:
              - user.provided.identifiable.contact
              - user.derived.identifiable.device.cookie_id
            data_use: improve_product_or_service
            data_subjects:
              - customer
            data_qualifier: identified_data
            dataset_references:
              - demo_users_dataset
        system_dependencies: []
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Int | Id of the organization this system belongs to |
| registry_id | Optional[Int] | Id of the registry this system belongs to |
| fides_key | FidesKey | A fides key is an identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and '_' |
| system_type | String | The type of system being declared |
| meta | Dict[String, String] | A key-value pair field to add various additional info |
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

=== Example Manifest

    ```yaml
    dataset:
      - organization_fides_key: 1
        fides_key: demo_users_dataset
        name: Demo Users Dataset
        description: Data collected about users for our analytics system.
        dataset_type: MySQL
        location: US East
        fields:
          - name: first_name
            description: User's first name
            path: demo_users_dataset.first_name
            data_categories:
              - user.provided.identifiable.name
          - name: email
            description: User's Email
            path: demo_users_dataset.email
            data_categories:
              - user.provided.identifiable.contact.email
          - name: state
            description: User's State
            path: demo_users_dataset.state
            data_categories:
              - user.provided.identifiable.contact.state
          - name: food_preference
            description: User's favorite food
            path: demo_users_dataset.food_preference
            data_categories:
              - user.provided.nonidentifiable
          - name: created_at
            description: User's creation timestamp
            path: demo_users_dataset.created_at
            data_categories:
              - system.operations
          - name: uuid
            description: User's unique ID
            path: demo_users_dataset.uuid
            data_categories:
              - user.derived.identifiable.unique_id
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Int | Id of the organization this system belongs to |
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

=== Example Manifest

    ```yaml
    policy:
      - organization_fides_key: 1
        fides_key: demo_privacy_policy
        name: Demo Privacy Policy
        description: The main privacy policy for the organization.
        rules:
          - organization_fides_key: 1
            fides_key: reject_direct_marketing
            name: Reject Direct Marketing
            description: Disallow collecting any user contact info to use for marketing.
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
    ```

| Name | Type | Description |
| --- | --- | --- |
| organization_fides_key | Int | Id of the organization this system belongs to |
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

=== Matching Rule

    ```yaml
    # Example Privacy Rule:
    - fides_key: reject_direct_marketing
      name: Reject Direct Marketing
      description: Disallow collecting any user contact info to use for marketing.
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

    # Example Privacy Declaration:
    - name: Collect data for marketing
      data_categories:
        - user.provided.identifiable.contact
        - user.derived.identifiable.device.cookie_id
      data_use: marketing_advertising_or_promotion
      data_subjects:
        - customer
      data_qualifier: identified_data

    # Example Evaluation Logic:

    - Do ANY of the data_categories match?
        - Yes
    - Do ANY of the data_uses match?
        - Yes
    - Do ANY of the data_subjects match?
        - Yes
    - Is the dataQualifier at the same level of exposure or higher?
        - Yes
    - Was the answer yes to all of the above questions?
        - Yes
    There is a match, and the Privacy Declaration evaluates to REJECT!
    ```

=== Non-Matching Rule

    ```yaml
    # Example Privacy Rule:
    - fides_key: reject_direct_marketing
      name: Reject Direct Marketing
      description: Disallow collecting any user contact info to use for marketing.
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

    # Example Privacy Declaration:
    - name: Collect data for marketing
      data_categories:
        - user.derived.identifiable.device.cookie_id
      data_use: marketing_advertising_or_promotion
      data_subjects:
        - customer
      data_qualifier: identified_data

    # Example Evaluation Logic:

    - Do ANY of the data_categories match?
        - No
    - Do ANY of the data_uses match?
        - Yes
    - Do ANY of the data_subjects match?
        - Yes
    - Is the data_qualifier at the same level of exposure or higher?
        - Yes
    - Was the answer yes to all of the above questions?
        - No
    There is no match!
    ```

When evaluating against a policy, Fides evaluates all privacy rules and takes the _most_ restrictive position.

---
