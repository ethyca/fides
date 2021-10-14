# Data Use Categories Reference

Data Use Categories are labels that describe how, or for what purpose(s) a component of your system is using data.

!!! Note "Extensibility and Interopability"
    Data Use Categories in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944. 
    
    You can extend the taxonomy to support your organization's needs. If you do this, we recommend extending from the existing categories to ensure interopability inside and outside your organization.

    If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues)


## Top Level Data Use Categories

There are seven top-level Data Use classes:

| Label                                          | Parent Key                 | Description                                                                                          |
| ---                                            | ---                         | ---                                                                                                  |
|`provide`                                       |`-`                         |Provide, give, or make available the product, service, application or system.                                                                                                      |
|`improve`                                       |`-`                         |Improve the product, service, application or system.                                                                                                                               |
|`personalize`                                   |`-`                         |Personalize the product, service, application or system.                                                                                                                           |
|`advertising`                                   |`-`                         |The promotion of products or services targeted to users based on the the processing of user provided data in the system.                                                           |
|`third_party_sharing`                           |`-`                         |The transfer of specified data categories to third parties outside of the system/application's scope.                                                                              |
|`collect`                                       |`-`                         |Collecting and storing data in order to use it for another purpose such as data training for ML.                                                                                   |
|`train_ai_system`                               |`-`                         |Training an AI system. Please note when this data use is specified, the method and degree to which a user may be directly identified in the resulting AI system should be appended.|


For each top level classification there are multiple subclasses that provide richer context.
Below is a reference for all subclasses of `account`, `system` and `user` to assist with describing all data across systems.

### Provide Data Uses

| Label                                          | Parent Key                        | Description                                                                                          |
| ---                                            | ---                               | ---                                                                                                  |
|`system`                                        |`provide`                          |The source system, product, service or application being provided to the user.                                                                                                     |
|`provide.system.operations`                     |`provide.system`                   |Use of specified data categories to operate and protect the system in order to provide the service.                                                                                |
|`provide.system.operations.support`             |`provide.system.operations`        |Use of specified data categories to provide support for operation and protection of the system in order to provide the service.                                                    |
|`provide.system.operations.support.optimization`|`provide.system.operations.support`|Use of specified data categories to optimize and improve support operations in order to provide the service.                                                                       |
|`provide.system.upgrades`                       |`provide.system`                   |Offer upgrades or upsales such as increased capacity for the service based on monitoring of service usage.                                                                         |

### Improve Data Uses

| Label     | Parent Key  | Description                                                       |
| ---       | ---         | ---                                                               |
|`system`   | `improve`   |The source system, product, service or application being improved. |


### Personalize Data Uses

| Label    | Parent Key    | Description                                                             |
| ---      | ---           | ---                                                                     |
|`system`  | `personalize` | The source system, product, service or application being personalized.  |


### Advertising Data Uses

| Label         | Parent Key                        | Description                                                                                                                                   |
| ---           | ---                               | ---                                                                                                                                           |
|`first_party`  | `advertising`                     | The promotion of products or services targeting users based on processing of derviced data from prior use of the system.                      |
|`contextual`   | `advertising.first_party`         | The promotion of products or services targeted to users based on the processing of derived data from the users prior use of the services.     |
|`personalized` | `advertising.first_party`         | The targeting and changing of promotional content based on processing of specific data categories from the user.                              |
|`third_party`  | `advertising`                     | The promotion of products or services targeting users based on processing of specific categories of data acquired from third party sources.   |
|`personalized` | `advertising.third_party`         | The targeting and changing of promotional content based on processing of specific categories of user data acquired from third party sources.  |


### Third Party Sharing Data Uses

| Label                     | Parent Key                         | Description                                                                                    |
| ---                       | ---                                | ---                                                                                            |
|`payment_processing`       | `third_party_sharing`              | Sharing of specified data categories with a third party for payment processing.                |
|`personalized_advertising` | `third_party_sharing`              | Sharing of specified data categories for the purpose of marketing/advertising/promotion.       |
|`fraud_detection`          | `third_party_sharing`              | Sharing of specified data categories with a third party fo fraud prevention/detection.         |
|`legal_obligation`         | `third_party_sharing`              | Sharing of data for legal obligations, including contracts, applicable laws or regulations.    |

### Collection & AI Training Data Uses

In the case of `collection` and `train_ai_system`, you will see these have no subclasses at present however define very specific data use cases that should be captured in data processes if they occur. 

| Label                | Parent Key  | Description                                                                                                                                                                          |
| ---                  | ---         | ---                                                                                                                                                                                  |
|`collect`             | `-`         | Collecting and storing data in order to use it for another purpose such as data training for ML.                                                                                     |
|`train_ai_system`     | `-`         | Training an AI system. Please note when this data use is specified, the method and degree to which a user may be directly identified in the resulting AI system should be appended.  |
