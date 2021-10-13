# Data Categories Reference

Data Categories are labels to describe the type of data processed by a system. You can assign one or more data categories to a field when classifying a system.

!!! Note "Extensibility and Interopability"
    Data Categories in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944. 
    
    You can extend the taxonomy to support your system needs. If you do this, we recommend extending from the existing class structures to ensure interopability inside and outside your organization.

    If you have suggestions for core classes that should ship with the taxonomy, please submit your requests here (**needs link to feature requests**).


## Top Level Data Categories

There are three top-level categories:


| Label     | Parent Key    | Description                                           |
| ---       | ---           | ---                                                   |
| `account` | `-`           | Data related to an account on the system.             |
| `system`  | `-`           | Data unique to, and under control of the system.      |
| `user`    | `-`           | Data related to the user of the system.               |

For each top level classification there are multiple subclasses that provide richer context.
Below is a reference for all subclasses of `account`, `system` and `user` to assist with describing all data across systems.

## Account Data Categories

### Account Contact Data

| Label             | Parent Key        | Description                               |
| ---               | ---               | ---                                       |
| `contact`         | `account`	        | Contact data related to a system account. |
| `city`            | `account.contact`	| Account's city level address data.        |
| `country`         | `account.contact`	| Account's country level address data.     |
| `email`           | `account.contact`	| Account's email address.                  |
| `phone_number`    | `account.contact`	| Account's phone number.                   |
| `postal_code`     | `account.contact`	| Account's postal code.                    |
| `state`           | `account.contact`	| Account's state level address data.       |
| `street`          | `account.contact`	| Account's street level address.           |

### Account Payment Data

| Label                         | Parent Key        | Description                               |
| ---                           | ---               | ---                                       |
| `payment`                     | `account`    	    | Payment data related to system account.   |
| `financial_account_number`    | `account.payment` | Payment data related to system account.   |

## System Data Categories

| Label             | Parent Key    | Description                               |
| ---               | ---           | ---                                       |
| `authentication`  | `system`      | Data used to manage access to the system. |
| `oeprations`      | `system` 	    | Data used for system operations.          |

## User Data Categories

The User Data classification has two inportant subclasses, for `derived` and `provided` data. 
In turn, `derived` and `provided` both have subclasses for `identifiable` and `nonidentifiable` data.

### User Derived Data

| Label                             | Parent Key                                | Description                                                                                   |
| ---                               | ---                                       | ---                                                                                           |
| `user.derived`                    | `user`                                    |Data derived from user provided data or as a result of user actions in the system.             |
| `identifiable`                    | `user.derived`                            |Derived data that is linked to, or identifies a user.                                          |
| `biometric_health`                | `user.derived.identifiable`               |Encoded characteristic collected about a user.                                                 |
| `browsing_history`                | `user.derived.identifiable`               |Content browsing history of a user.                                                            |
| `contact`                         | `user.derived.identifiable`               |Contact data collected about a user.                                                           |
| `demographic`                     | `user.derived.identifiable`               |Demographic data about a user.                                                                 |
| `gender`                          | `user.derived.identifiable`               |Gender of an individual.                                                                       |
| `location`                        | `user.derived.identifiable`               |Records of the location of a user.                                                             |
| `media_consumption`               | `user.derived.identifiable`               |Media type consumption data of a user.                                                         |
| `non_specific_age`                | `user.derived.identifiable`               |Age range data.                                                                                |
| `observed`                        | `user.derived.identifiable`               |Data collected through observation of use of the system.                                       |
| `organization`                    | `user.derived.identifiable`               |Derived data that is linked to, or identifies an organization.                                 |
| `profiling`                       | `user.derived.identifiable`               |Preference and interest data about a user.                                                     |
| `race`                            | `user.derived.identifiable`               |Racial or ethnic origin data.                                                                  |
| `religious_belief`                | `user.derived.identifiable`               |Religion or religious belief.                                                                  |
| `search_history`                  | `user.derived.identifiable`               |Records of search history and queries of a user.                                               |
| `sexual_orientation`              | `user.derived.identifiable`               |Personal sex life or sexual data.                                                              |
| `social`                          | `user.derived.identifiable`               |Social activity and interaction data.                                                          |
| `telemetry`                       | `user.derived.identifiable`               |User identifiable measurement data from system sensors and monitoring.                         |
| `unique_id`                       | `user.derived.identifiable`               |Unique identifier for a user assigned through system use.                                      |
| `user_sensor`                     | `user.derived.identifiable`               |Measurement data derived about a user's environment through system use.                        |
| `workplace`                       | `user.derived.identifiable`               |Organization of employment.                                                                    |
| `device`                          | `user.derived.identifiable`               |Data related to a user's device, configuration and setting.                                    |
| `cookie_id`                       | `user.derived.identifiable.device`        |Cookie unique identification number.                                                           |
| `device_id`                       | `user.derived.identifiable.device`        |Device unique identification number.                                                           |
| `ip_address`                      | `user.derived.identifiable.device`        |Unique identifier related to device connection.                                                |
| `nonidentifiable`                 | `user.derived`                            |Non-user identifiable data derived related to a user as a result of user actions in the system.|
| `nonsensor`                       | `user.derived.nonidentifiable`            |Non-user identifiable measurement data derived from sensors and monitoring systems.            |

### User Provided Data

| Label                             | Parent Key                                | Description                                                                                   |
| ---                               | ---                                       | ---                                                                                           |
| `provided`                        | `user`                                    |Data provided or created directly by a user of the system.                                     |
| `identifiable`                    | `user.provided`                           |Data provided or created directly by a user that is linked to or identifies a user.            |
| `biometric`                       | `user.provided.identifiable`              |Encoded characteristics provided by a user.                                                    |
| `childrens`                       | `user.provided.identifiable`              |Data relating to children.                                                                     |
| `health_and_medical`              | `user.provided.identifiable`              |Health records or individual's personal medical information.                                   |
| `job_title`                       | `user.provided.identifiable`              |Professional data.                                                                             |
| `name`                            | `user.provided.identifiable`              |User's real name.                                                                              |
| `non_specific_age`                | `user.provided.identifiable`              |Age range data.                                                                                |
| `political_opinion`               | `user.provided.identifiable`              |Data related to the individual's political opinions.                                           |
| `race`                            | `user.provided.identifiable`              |Racial or ethnic origin data.                                                                  |
| `religious_belief`                | `user.provided.identifiable`              |Religion or religious belief.                                                                  |
| `sexual_orientation`              | `user.provided.identifiable`              |Personal sex life or sexual data.                                                              |
| `workplace`                       | `user.provided.identifiable`              |Organization of employment.                                                                    |
| `date_of_birth`                   | `user.provided.identifiable`              |User's date of birth.                                                                          |
| `gender`                          | `user.provided.identifiable`              |Gender of an individual.                                                                       |
| `genetic`                         | `user.provided.identifiable`              |Data about the genetic makeup provided by a user.                                              |
| `contact`                         | `user.provided.identifiable`              |User provided contact data for purposes other than account management.                         |
| `city`                            | `user.provided.identifiable.contact`      |User's city level address data.                                                                |
| `country`                         | `user.provided.identifiable.contact`      |User's country level address data.                                                             |
| `email`                           | `user.provided.identifiable.contact`      |User's provided email address.                                                                 |
| `phone_number`                    | `user.provided.identifiable.contact`      |User's phone number.                                                                           |
| `postal_code`                     | `user.provided.identifiable.contact`      |User's postal code.                                                                            |
| `state`                           | `user.provided.identifiable.contact`      |User's state level address data.                                                               |
| `street`                          | `user.provided.identifiable.contact`      |User's street level address data.                                                              |
| `credentials`                     | `user.provided.identifiable`              |User provided authentication data.                                                             |
| `biometric_credentials`           | `user.provided.identifiable.credentials`  |Credentials for system authentication.                                                         |
| `password`                        | `user.provided.identifiable.credentials`  |Password for system authentication.                                                            |
| `financial`                       | `user.provided.identifiable`              |Payment data and financial history.                                                            |
| `account_number`                  | `user.provided.identifiable.financial`    |User's account number for a payment card, bank account, or other financial system.             |
| `government_id`                   | `user.provided.identifiable`              |State provided identification data.                                                            |
| `drivers_license_number`          | `user.provided.identifiable.government_id`|State issued driving identification number.                                                    |
| `national_identification_number`  | `user.provided.identifiable.government_id`|State issued personal identification number.                                                   |
| `passport_number`                 | `user.provided.identifiable.government_id`|State issued passport data.                                                                    |
| `nonidentifiable`                 | `user.provided`                           |Data provided or created directly by a user that is not identifiable.                          |