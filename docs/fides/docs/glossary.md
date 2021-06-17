# Fides Privacy Glossary

## Privacy Classifiers

Fides uses four classifiers for describing how systems use privacy data, and for describing what privacy data can be used in what ways. All of these types are initially populated within the server but are extensible with custom values. All of these types support organization into hierarchical trees.

### Data category

```yaml
- customer content data
    - credentials
    - personal health data
    - ...
- derived data
    - end user identifiable information
        - elemetry data
        - connectivity data
        -  ...
- account data
    - account or administration contact information
    - payment instrument data
    -  ...
```

### Data use

```yaml
- personalize
- share
  - share when required to provide the service
- promote
  - promote based on contextual information
  - promote based on personalization
```

### Data Subject Category

```yaml
- customer
- supplier
- job applicant
- ...
```

### Data qualifier

```yaml
- aggregated data
  - anonymized data
    - unlinked pseudonymized data
      - pseudonymized data
        - identified data
```

Data qualifiers are sorted in order of increasing data exposure.

## Systems

A system represents the privacy usage of a single software project or codebase, made up of a few constituent parts:

### Datasets

A dataset represents an annotated datastore (see below). It is ultimately made up of a collection of tables and fields. Each field declares a list of data categories it represents as well as a data qualifier.

If the privacy range of datasets is wider than that declared by this system a warning will be generated.

### Dependent Systems

System dependencies are a graph, giving users the ability to describe that system `A` is dependent on systems `B` and `C`. Fides will then merge all of the systems' declarations and ensure that not only does system `A` perform in a compliant manner, but that systems `B` and `C` do as well.

### Declarations

This individual system's privacy usage. Each declaration consists of

```yaml
- A set of data categories
- A set of data subject categories
- A data use
- A data qualifier
```

And can be read as "This system uses data in categories [data categories] (for [data subject categories]) with the purpose of (data use) at a qualified privacy level of (data qualifier)"
A system can have multiple declarations.

```json
{
   "id":9,
   "organizationId":1,
   "registryId":5,
   "fidesKey":"an-organization-unique-identifier-for-this-system",
   "versionStamp":26, //a by-organization global version numbering. Any changes to the data held by an organization increment the organization version stamp.
   "fidesSystemType":"DATABASE", //the type of system this represents
   "name":"an optional human-readable name",
   "description":"an optional description.",
   //declarations of privacy useage:
   "declarations":[
      {
         "dataCategories":[
            "credentials"
         ],
         "dataUse":"provide",
         "dataQualifier":"identified_data",
         "dataSubjectCategories":[
            "prospect"
         ]
      },
      {
         "dataCategories":[
            "telemetry_data",
            "connectivity_data"
         ],
         "dataUse":"share",
         "dataQualifier":"identified_data",
         "dataSubjectCategories":[
            "prospect"
         ]
      },
      {
         "dataCategories":[
            "payment_instrument_data",
            "account_or_administration_contact_information"
         ],
         "dataUse":"improvement_of_business_support_for_contracted_service",
         "dataQualifier":"identified_data",
         "dataSubjectCategories":[
            "prospect"
         ]
      }
   ],
   "systemDependencies":[
      "system2",
      "test_system_2",
      "test_system_1"
   ],
   "datasets":[
      "d1"
   ],
   "creationTime":"2021-05-20T23:50:14Z",
   "lastUpdateTime":"2021-05-20T23:50:14Z"
}
```

## Policies

### Policy rules

Aside from some identifing data, a policy is made up of a collection of rules. Each rule specifies an action:
a data qualifer as well as, for each of

```yaml
- data uses
- data categories
- data subject categories
both
- a list of values
- a qualifier (ANY, ALL, or NONE)
```

where something like, e.g.

```json
{
   "dataCategories":{
      "inclusion":"ANY",
      "values":[
         "account_data",
         "derived_data"
      ]
   }
}
```

means "this rule applies if the data categories being considered match ANY of "account_data", "derived_data" (child values are considered to be matching)

#### Policy Rule Actions

Currently

```yaml
- ACCEPT (accept if the policy matches)
- REJECT (reject if the policy matches)
- MANUAL (trigger a manual review process, TBD)
```

#### Policy Rule Application

A policy rule _applies_ to a system if

- the system matches the rule's categories
- the system matches the rule's uses
- the system matches the rule's data subject categories
- the system qualifier matches the rule's qualifier

To evaluate a system against a policy, we evaluate all rules and take the _most_ restricive interpretation.

### A Complete Policy

```json
{
   "id":2,
   "organizationId":1,
   "fidesKey":"an-organization-unique-identifier-for-this-policy",
   "versionStamp":3,
   "rules":[
      {
         "id":3,
         "organizationId":1,
         "policyId":2,
         "fidesKey":"an-organization-unique-identifier-for-this-policy-rule",
         "dataCategories":{
            "inclusion":"ANY",
            "values":[
               "profiling_data",
               "account_data",
               "derived_data",
               "cloud_service_provider_data",
            ]
         },
         "dataUses":{
            "inclusion":"ANY",
            "values":[
               "market_advertise_or_promote",
               "offer_upgrades_or_upsell",
            ]
         },
         "dataSubjectCategories":{
            "inclusion":"ANY",
            "values":[
               "trainee",
               "commuter"
            ]
         },
         "dataQualifier":"pseudonymized_data",
         "action":"REJECT",
         "creationTime":"2021-05-20T22:26:58Z",
         "lastUpdateTime":"2021-05-20T22:26:58Z"
      },
      {
         "id":4,
         "organizationId":1,
         "policyId":2,
         "fidesKey":"rule1",
         "dataCategories":{
            "inclusion":"ANY",
            "values":[
               "user_location",
               "personal_health_data_and_medical_records",
               "connectivity_data",
               "credentials"
            ]
         },
         "dataUses":{
            "inclusion":"ALL",
            "values":[
               "improvement_of_business_support_for_contracted_service",
               "personalize",
               "share_when_required_to_provide_the_service"
            ]
         },
         "dataSubjectCategories":{
            "inclusion":"NONE",
            "values":[
               "trainee",
               "commuter",
               "patient"
            ]
         },
         "dataQualifier":"pseudonymized_data",
         "action":"REJECT",
         "creationTime":"2021-05-20T22:26:58Z",
         "lastUpdateTime":"2021-05-20T22:26:58Z"
      }
   ],
   "creationTime":"2021-05-20T22:26:58Z",
   "lastUpdateTime":"2021-05-20T22:26:58Z"
}
```

## Approvals
We evaluate both systems and registries. Since a registry is essentially a graph of systems, a registry evaluation is just an evaluation of each individual system along with a few additional checks on the system graph as a whole.

When the evaluation of a system manifest is triggered, the following checks are run:

- If the systems privacy declarations are narrower than the declared privacy exposure of its dependent datasets, we generate a warning. For example, the system declares that it uses a dataset that includes "customer content data" at the "anonymized" level, but the system doesn't declare that it's exposing that.
- If the system's privacy declarations are narrower than the declared privacy exposure of a dependent system, we generate a warning. This is similar to the above restriction, except that we examine the privacy declarations of a dependant system rather than a dataset.
- For each policy rule we check each system declaration and take action on any declaration that falls within that policy rule's scope. For example, if a policy rule declares that **profiling_data** that is **identified_data** is disallowed, and the system contains a declaration that includes such data, an error will be generated.

Additionally, when a registry is evaluated, we also check that

- The registry system graph contains a dependency cycle (that is, **system_a** declares that it depends on **system_b** that declares that it depends on **system_a**).
- A system declares a dependency on a system that is not referenced in the registry.


### A sample approval

```json
{
  "id":40,
  "organizationId":1,
  "registryId":20,
  "userId":1,
  "versionStamp":216,
  "action":"evaluate",
  //the overall response status. This will be the worst of any individual system responses in descending order:
  // ERROR: at least one component was invalid; the registry can't be evaluated
  // FAIL: at least one component failed validation
  // MANUAL: at least one component requires manual approval
  // PASS: none of the above conditions were found
  "details":{
    "overall":{
      "FAIL":[
        "system1"
      ],
      "ERROR":[
        "system3"
      ]
    },
    "evaluations":{
      "system1":{
        "FAIL":{
          "policy2.rule3":[
            "test1",
            "test2",
            "test3"
          ],
          "policy1.rule2":[
            "test1",
            "test2",
            "test3"
          ],
          "policy1.rule1":[
            "test1",
            "test2",
            "test3"
          ],
          "policy2.rule4":[
            "test1",
            "test2",
            "test3"
          ]
        },
        "warnings":[
          "Dataset:d1: These categories exist for qualifer identified_data in this dataset but do not appear with that qualifier in the dependant system system1:[customer_content_data,derived_data,cloud_service_provider_data]",
          These categories exist for qualifer identified_data in the declared dataset d1a but do not appear with that qualifier in the dependant system:[profiling_data,political_opinions,demographic_information,user_location,personal_health_data_and_medical_records],
        "errors":[

        ]
      },
      "system3":{
        "warnings":[

        ],
        "errors":[
          "The referenced datasets missing_dataset_1,missing_dataset_2 were not found.",
          "The referenced datasets system2 were not found."
        ]
      }
    },
    "warnings":[
      "The referenced objects don't exist in the given values:system2",
      "cyclic reference: system3->system3"
    ]
  }
}
```
