# Fides Resource Types

You define your privacy policies by creating sets of resources. There are nine resource types divided into two groups:

<table>
  <thead>
    <tr>
      <th>Group</th>
      <th>Resource types</th>
      <th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Structure</td>
      <td>Organization<br>Policy<br>System<br>Registry<br>Dataset</td>
      <td>Provides a structure for your policies and the data to which they're applied.</td>
    </tr>
    <tr>
      <td>Data</td>
      <td>Data category<br>Data use<br>Data subject<br>Data qualifier</td>
      <td>The elements that you use to create a privacy policy. These resources describe the conditions in which a specific type of user is allowed to view a particular type of data.</td>
    </tr>
  </tbody>
</table>

The rest of this document...etc

## How to ingest your resources

- CLI
- API

## Resource Specifications

### Organization

An organization represents all or part of an enterprise or company. It establishes the root of your resource hierarchy. This means that while you can have more than organization resource, they can't refer to each other's sub-resources. For example, your "American Stores" organization can't refer to the Policy objects that are defined by your "European Stores" organization.

### Specification

<table class="hierarchy">
  <tr class="element">
    <td class="property">fides_key<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A string token of your own invention that uniquely identifies this organization. It's your responsibility to ensure that the value is unique across all of your organization objects.
      The value may only contain alphanumeric characters and '_'.
    </td>

  </tr>
    <tr class="element">
    <td class="property">name<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A UI-friendly name of the organization.
    </td>
  </tr>

  <tr class="element">
    <td class="property">description<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A description of the organization.
    </td>
  </tr>
  <tr class="element">
    <td class="property"><span class="nest"/>description<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr class="element">
    <td class="description"><span class="bump"/>
      A description of the organization.
    </td>
  </tr>
</table>


### Manifest File

**Demo manifest:** None. Fides automatically defines a default organization with a `fides_key` value of `organization_1`.

```yaml
organization:
  fides_key: organization_1
  name: Acme Incorporated
  description: An organization that represents all of Acme Inc.
```

**API Payload**
```json
{
  "fides_key": "organization_1",
  "name": "Acme Incorporated",
  "description": "An organization that represents all of Acme Inc."
}

```

---

## Privacy Classifiers

Fides uses four classifiers for describing how systems use privacy data, and for describing what privacy data can be used in what ways. All of these types support organization into hierarchical trees.

### Data Category

A Data Category describes the real-world attribute that the data describes: date of birth, tax ID, home address, and so on.

**Example Manifest**

```yaml
data_category:
- fides_key: user.provided.identifiable.date_of_birth
  name: Date of Birth
  parent_key: user.provided.identifiable
  description: User's date of birth.
```

**Example Hierarchy**

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

**Example Manifest**

```yaml
data_use:
- fides_key: provide.system.operations.support
  name: Operations Support
  parent_key: provide.system.operations
```

**Example Hierarchy**

```yaml
- provide
  - provide.system
    - provide.system.operations
      - provide.system.operations.support
    - provide.system.upgrades
- third_party_sharing
  - third_party_sharing.payment_processing
  - third_party_sharing.personalized_advertising
  - third_party_sharing.fraud_detection
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

**Example Manifest**

```yaml
data_subject:
- fides_key: anonymous_user
  name: Anonymous User
  description: A user without any identifiable information tied to them.
```

**Example Hierarchy**

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

**Example Manifest**

```yaml
data_qualifier:
- fides_key: aggregated_data
  name: Aggregated Data
  description: Aggregated data is statistical data that does not contain individual-level entries and is combined from information about enough different persons that individual-level attribtures are not identifiable.
```

**Example Hierarchy**

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

**Example Manifest**

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

**Example Manifest**

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
        data_use: improve.system
        data_subjects:
          - customer
        data_qualifier: identified_data
        dataset_references:
          - demo_users_dataset
    system_dependencies: []
```

<table class="hierarchy">
  <tr class="element">
    <td class="property">fides_key<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A string token that uniquely identifies thus system. The value may only contain alphanumeric characters and '_'.
    </td>
  </tr>
    <tr class="element">
    <td class="property">organization_fides_key<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      The `fides_key` value of the organization to which this system belongs.
    </td>
  </tr>
    <tr class="element">
    <td class="property">name<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      UI-friendly name of the system.
    </td>
  </tr>

  <tr class="element">
    <td class="property">description<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A description of the system.
    </td>
  </tr>

  </tr>
    <tr class="element">
    <td class="property">system_type<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A string token of your own invention that classifies the system.
    </td>
  </tr>

</tr>
    <tr class="element">
    <td class="property">meta<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr>
    <td class="description">
      A string token of your own invention that classifies the system.
    </td>
  </tr>
  <tr class="element">
    <td class="property"><span class="nest"/>description<span class="required"/>&nbsp;&nbsp;<span class="data-type">string</td>
  </tr>
  <tr class="element">
    <td class="description"><span class="bump"/>
      A description of the organization.
    </td>
  </tr>
</table>

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

**Example Manifest**

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

## Policy

A policy combines a set of privacy rules. Your system and registry resources are evaluated against your policies to ensure compliance.

**Example Manifest**

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
            - advertising
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

**Matching Rule**

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
      - advertising
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
  data_use: advertising
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

**Non-Matching Rule**

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
      - advertising
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
  data_use: advertising
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


## Resource Relationship Diagram

![alt text](../img/Resource_Relations.svg "Fides Manifest Workflow")

