# Data Categories Reference

Data Categories are hierarchical labels used to describe the type of data processed by your software. Data Category objects form a hierarchy: A Data Category can contain any number of children, but a given Category may only have one parent. You assign a child Category to a parent by setting the child's `parent_key` property. For example, the `user.job_title` Category is used for personally-identifiable job title information for a user.

These are most heavily used by the System and Dataset resources, where you can assign one or more data categories to each field.

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_constrained string_

A string token that uniquely identifies this Data Category. The value is a dot-separated concatenation of the `fides_key` values of the resource's ancestors plus a final element for this resource:

`grandparent.parent.this_data_category`

The final element (`this_data_category`) may only contain alphanumeric characters and underscores (`[A-Za-z0-9_.-]`). The dot character is reserved as a separator.

**name**<span class="spacer"/>_string_

A UI-friendly label for the Data Category.

**description**<span class="spacer"/>_string_

A human-readable description of the Data Category.

**parent_key**<span class="spacer"/>_string_<span class="spacer"/>

The fides key of the Data Category's parent.

**organization_fides_key**<span class="spacer"/>_string_<span class="spacer"/>default: `default_organization`

The fides key of the organization to which this Data Category belongs.

!!! Note "Extensibility and Interopability"
    Data Categories in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944.

    You can extend the taxonomy to support your system needs. If you do this, we recommend extending from the existing categories to ensure interopability inside and outside your organization.

    If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues)

## Top Level Data Categories

There are three top-level categories:

| Label     | Parent Key    | Description                                           |
| ---       | ---           | ---                                                   |
| `system`  | `-`           | Data unique to, and under control of the system.      |
| `user`    | `-`           | Data related to the user of the system.               |

For each top level category there can be multiple subcategories that provide richer context.

Below is a reference for all subcategories of `system` and `user` to assist with describing all data across systems.

## System Data Categories

| Label             | Parent Key    | Description                               |
| ---               | ---           | ---                                       |
| `authentication`  | `system`      | Data used to manage access to the system. |
| `operations`      | `system`      | Data used for system operations.          |

## User Data Categories

| Label                             | Parent Key                                | Description                                                                                   |
| ---                               | ---                                       | ---                                                                                           |
| `biometric`                       | `user`                                    |Encoded characteristics of a user.                                                             |
| `biometric_health`                | `user`                                    |Encoded characteristic about a user's health.                                                  |
| `browsing_history`                | `user`                                    |Content browsing history of a user.                                                            |
| `contact`                         | `user`                                    |User contact data.                                                                             |
| `address`                         | `user.contact`                            |User contact data related to an address.                                                       |
| `city`                            | `user.contact.address`                    |User's city level address data.                                                                |
| `country`                         | `user.contact.address`                    |User's country level address data.                                                             |
| `email`                           | `user.contact.address`                    |User's email address.                                                                          |
| `phone_number`                    | `user.contact.address`                    |User's phone number.                                                                           |
| `postal_code`                     | `user.contact.address`                    |User's postal code.                                                                            |
| `state`                           | `user.contact.address`                    |User's state level address data.                                                               |
| `street`                          | `user.contact.address`                    |User's street level address data.                                                              |
| `demographic`                     | `user`                                    |Demographic data about a user.                                                                 |
| `gender`                          | `user`                                    |Gender of an individual.                                                                       |
| `location`                        | `user`                                    |Records of the location of a user.                                                             |
| `media_consumption`               | `user`                                    |Media type consumption data of a user.                                                         |
| `non_specific_age`                | `user`                                    |Age range data.                                                                                |
| `observed`                        | `user`                                    |Data collected through observation of use of the system.                                       |
| `organization`                    | `user`                                    |Derived data that is linked to, or identifies an organization.                                 |
| `profiling`                       | `user`                                    |Preference and interest data about a user.                                                     |
| `race`                            | `user`                                    |Racial or ethnic origin data.                                                                  |
| `religious_belief`                | `user`                                    |Religion or religious belief.                                                                  |
| `search_history`                  | `user`                                    |Records of search history and queries of a user.                                               |
| `sexual_orientation`              | `user`                                    |Personal sex life or sexual data.                                                              |
| `social`                          | `user`                                    |Social activity and interaction data.                                                          |
| `telemetry`                       | `user`                                    |User identifiable measurement data from system sensors and monitoring.                         |
| `unique_id`                       | `user`                                    |Unique identifier for a user assigned through system use.                                      |
| `user_sensor`                     | `user`                                    |Measurement data derived about a user's environment through system use.                        |
| `workplace`                       | `user`                                    |Organization of employment.                                                                    |
| `device`                          | `user`                                    |Data related to a user's device, configuration and setting.                                    |
| `cookie_id`                       | `user.device`                             |Cookie unique identification number.                                                           |
| `device_id`                       | `user.device`                             |Device unique identification number.                                                           |
| `ip_address`                      | `user.device`                             |Unique identifier related to device connection.                                                |
| `childrens`                       | `user`                                    |Data relating to children.                                                                     |
| `health_and_medical`              | `user`                                    |Health records or individual's personal medical information.                                   |
| `job_title`                       | `user`                                    |Professional data.                                                                             |
| `name`                            | `user`                                    |User's real name.                                                                              |
| `political_opinion`               | `user`                                    |Data related to the individual's political opinions.                                           |
| `date_of_birth`                   | `user`                                    |User's date of birth.                                                                          |
| `genetic`                         | `user`                                    |Data about the genetic makeup of a user.                                                       |
| `credentials`                     | `user`                                    |User authentication data.                                                                      |
| `biometric_credentials`           | `user.credentials`                        |Credentials for system authentication.                                                         |
| `password`                        | `user.credentials`                        |Password for system authentication.                                                            |
| `financial`                       | `user`                                    |Payment data and financial history.                                                            |
| `account_number`                  | `user.financial`                          |User's account number for a payment card, bank account, or other financial system.             |
| `government_id`                   | `user`                                    |State provided identification data.                                                            |
| `drivers_license_number`          | `user.government_id`                      |State issued driving identification number.                                                    |
| `national_identification_number`  | `user.government_id`                      |State issued personal identification number.                                                   |
| `passport_number`                 | `user.government_id`                      |State issued passport data.                                                                    |
| `nonidentifiable`                 | `user`                                    |Non-user identifiable data related to a user as a result of user actions in the system.        |
