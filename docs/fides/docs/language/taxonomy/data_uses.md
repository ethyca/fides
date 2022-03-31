# Data Uses Reference

A Data Use is a label that denotes the way data is used in your system: "Advertising, Marketing or Promotion", "First Party Advertising", and "Sharing for Legal Obligation", as examples.

Data Use objects form a hierarchy: A Data Use can contain any number of children, but a given Data Use may only have one parent. You assign a child Data Use to a parent by setting the child's `parent_key` property. For example, the `third_party_sharing.personalized_advertising` Data Use type is data used for personalized advertising when shared with third parties.

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_constrained string_

A string token that uniquely identifies this Data Use. The value is a dot-separated concatenation of the `fides_key` values of the resource's ancestors plus a final element for this resource:

`grandparent.parent.this_data_use`

The final element (`this_data_use`) may only contain alphanumeric characters and underscores (`[A-Za-z0-9_.-]`). The dot character is reserved as a separator.

**name**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A UI-friendly label for the Data Use.

**description**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

A human-readable description of the Data Use.

**parent_key**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_<span class="spacer"/>

The fides key of the the Data Use's parent.

**legal_basis**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_enum_<span class="spacer"/>

The legal basis category of which the data use falls under. This field is used as part of the creation of an exportable data map. Current valid options:

* `Consent`
* `Contract`
* `Legal Obligation`
* `Vital Interest`
* `Public Interest`
* `Legitimate Interest`

**special_category**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_enum_

The special category for processing of which the data use falls under. This field is used as part of the creation of an exportable data map. Current valid options:

* `Consent`
* `Employment`
* `Vital Interests`
* `Non-profit Bodies`
* `Public by Data Subject`
* `Legal Claims`
* `Substantial Public Interest`
* `Medical`
* `Public Health Interest`

**recipent**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_

An array of recipients is applied here when sharing personal data outside of your organization (e.g. Internal Revenue Service, HMRC, etc.)

**legitimate_interest**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;boolean<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;default: `False`

A boolean value representing whether the legal basis is a `Legitimate Interest`. This is validated at run time and looks for a `legitimate_interest_impact_assessment` to exist if true.

**legitimate_interest_impact_assessment**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_url_

A url to the legitimate interest impact assessment. Can be any valid url (e.g. http, file, etc.)

**organization_fides_key**<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_string_<span class="spacer"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;default: `default_organization`

The fides key of the organization to which this Data Use belongs.

!!! Note "Extensibility and Interoperability"
    Data Uses in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944.

    You can [extend the taxonomy](./../../guides/extending_taxonomy.md) to support your organization's needs. If you do this, we recommend extending from the existing categories to ensure interoperability inside and outside your organization.

    If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues).

## Top Level Data Uses

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
