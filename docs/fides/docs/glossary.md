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

## Registry

A registry represents a collection of systems. Since systems can declare their dependencies on other systems, this is essentially a system graph.
Validations of a registry validate all systems indidually, as well as validate their declarations in light of their dependencies.

## Approvals

### Approval Validation Checks

Evaluations of systems and registries may potentially generate a list of errors and warnings.

- Any errors will result in a `FAIL` response.
- Warnings will have no effect.

Some sources of errors or warnings:

```yaml
- errors
 - dependency on a system that doesn't exist, or isn't part of the registry
 - dependency on a dataset that doesn't exist
 - dependency on self (loop)
 - dependency loop between multiple systems
 
- warnings.
 - system declarations return narrower privacy range than included in datasets (i.e. dataset includes data that's "customer content data", at the "anonymized" level, but the system doesn't declare that it's exposing that).
 - system A declares a dependency on system B, but system B has been more recently been validated (that is, the privacy declarations of system B may have been changed)
 - system A declares a dependency on dataset B, but dataset B has been more recently been validated
```

### A sample approval

```json
{
  "id":48,
  "organizationId":1,
  "registryId":32,
  "userId":1,
  "versionStamp":244,
  "action":"rate", // we'll probably have a bunch of different "submit" actions - i.e. dry-run, create, update, ... TBD
  "status":"FAIL", // this is the overall result. we should get the most restrictive; that is, if any component is FAIL, the overall is FAIL
  "details":{
    "FAIL":{
      "system1a":{
        "policy2a":{
          "declarations":{
            "rule4":[  // this means that policy2a, rule4 failed system declarations 0, 1, and 2. 
              0,       // this is pretty opaque, maybe naming the declarations would be helpful
              1,
              2
            ],
            "rule3":[
              0,
              1,
              2
            ]
          }
        },
        "policy1-b":{
          "declarations":{
            "rule1":[
              0,
              1,
              2
            ],
            "rule2":[
              0,
              1,
              2
            ]
          }
        },
        "policy1a":{
          "declarations":{
            "rule1":[
              0,
              1,
              2
            ],
            "rule2":[
              0,
              1,
              2
            ]
          }
        }
      },
      "system2a":{
        "policy2a":{
          "declarations":{
            "rule4":[
              0,
              1
            ],
            "rule3":[
              0,
              1
            ]
          }
        },
        "policy1-b":{
          "declarations":{
            "rule1":[
              0,
              1
            ],
            "rule2":[
              0,
              1
            ]
          }
        },
        "policy1a":{
          "declarations":{
            "rule1":[
              0,
              1
            ],
            "rule2":[
              0,
              1
            ]
          }
        }
      }
    },
    "PASS":{
      "system1a":{

      },
      "system2a":{

      },
      "system3a":{

      }
    }
  },
  "messages":{
    "errors":[
      "These systems were declared as dependencies but were not found :[test_system_2,test_system_1,system1-c]",
      "cyclic reference: system2a->system3a->system2a",
      "These datasets were declared as dependencies but were not found:[missing_dataset_2,missing_dataset_1,d2,d1]"
    ],
    "warnings":[
      "These categories exist for qualifer identified_data in the declared dataset d1a but do not appear with that qualifier in the dependant system system2a:[profiling_data,personal_biometric_data,account_data,derived_data,cloud_service_provider_data,personal_genetic_data,social_data,users_environmental_sensor_data,customer_contact_lists,search_commands_and_queries,financial_details,telemetry_data,customer_content_data,access_and_authentication_data,personal_data_of_children,biometric_and_health_data,connectivity_data,sensor_measurement_data,account_or_administration_contact_information,political_opinions,payment_instrument_data,content_consumption_data,end_user_identifiable_information,client_side_browsing_history,organization_identifiable_information,end_user_contact_data,observed_usage_of_the_service_capability,demographic_information,user_location,personal_health_data_and_medical_records]",
      "system2a declares the system system3a as a dependency, but system3a has been more recently updated than system2a",
      "These categories exist for qualifer identified_data in the declared dataset d1a but do not appear with that qualifier in the dependant system system1a:[profiling_data,political_opinions,account_data,derived_data,cloud_service_provider_data,personal_genetic_data,social_data,users_environmental_sensor_data,customer_contact_lists,search_commands_and_queries,financial_details,customer_content_data,access_and_authentication_data,personal_data_of_children,biometric_and_health_data,sensor_measurement_data,personal_biometric_data,operations_data,content_consumption_data,end_user_identifiable_information,client_side_browsing_history,organization_identifiable_information,end_user_contact_data,observed_usage_of_the_service_capability,demographic_information,user_location,personal_health_data_and_medical_records]"
    ]
  }
}
```
