# Exporting a data map using the demo resources


the purpose of this guide is to detail which attributes are required and how to implement them to export an Article 30 compliant Record of Processing Activites (RoPA).

To follow the guide, please follow [Step 1 of the Quickstart](https://github.com/ethyca/fides/#rocket-quick-start)

The rest of the guide will cover the following:

1. Export the `demo_resources` as they are
1. Review the resource and taxonomy properties used
1. Extend the default taxonomy (to fill in missing fields)
1. Export a mock Article 30 compliant RoPA


## Export the Demo Resources

At this point you should have completed [Step 1 of the Quickstart](https://github.com/ethyca/fides/#rocket-quick-start) and have a terminal window ready.

Let's apply and export the provided `demo_resources` and explore what our data map looks like.

```sh title="Apply and Export Defaults"
$ fidesctl apply demo_resources/
$ fidesctl export datamap demo_resources/
```

The data map should have been exported to the `demo_resources/` directory, open it and we can review each section.


### Organization

The header block at the top of a data map is composed of properties found in the Organization resource. For demo purposes, this resource has fake data but normally this would be composed of publicly available information for your company/organization.

![Organization Contact Info](../img/datamap_organization_contact.png)

Reviewing `demo_resources/demo_organization.yml` will highlight the relationship between the Organization resource manifest and the data map. Each of `controller`, `data_protection_officer`, and `representative` are composed of Contact Detail properties aligning with the exported data map.

Additionally, the link to the security policy of an organization can be found modeled on the Organization resource as `security_policy`.


### Dataset

The Dataset is primarily used to provide a list of Data Categories which populate the data map. Additional properties can optionally be applied for `retention` and `third_country_transfers`.

![Demo Dataset Properties](../img/demo_dataset_properties.png)


Reviewing `demo_resources/demo_dataset.yml` will highlight the relationship between the Organization resource manifest and the data map.

`data_categories` and `retention` can be set at any of  Dataset, DatasetCollection, or DatasetField. `third_country_transfers` should be set at the Dataset level.

Any Datasets referenced by a system will have this information exported as rows of your data map.


### System

The system houses the remainder of the attributes on our initial data map.

Each populated property is listed below with it's referenced property in `demo_system.yml`:

* **Fides dataset**: Found under `dataset_references`, used to join dataset(s) to the system.
* **Fides system**: The name defined at the top-level of the system.
* **Department or Business Function**: `administering_department` set at the top-level of the system.
* **Purpose of Processing**: The name defined for the `data_use` set in a Privacy Declaration.
* **Categories of Individuals**: The name defined for the `data_subject` set in a Privacy Declaration.
* **Categories of Personal Data**: Any Data Category set as part of a Privacy Declaration will also be populated here (see the output for Demo Marketing System as a clear example).
* **Role or Responsibility**: Defined by the `data_responsibility_title` property at the top-level of the system.
* **Source of the Personal Data**: The fides dataset name if referenced on the system.
* **Data Protection Impact Assessment**: All of the information related to a DPIA is defined under the `data_protection_impact_assessment` property at the top-level of the system.


## What's missing?

This next section focuses on the data map columns populated with `N/A` and how to use properties within the fides Taxonomy and Resources to replace those with value-added data required as part of a RoPA.

To do this, we need to extend the default taxonomy for our particular needs. The manifeset updates can be viewed in `demo_extended_taxonomy.yml`.

### Data Use

Below is our extended data use that we are going to apply to our Demo Marketing System. Each of these properties is responsible for populating a field on your data map.

```yml title="Extended Data Use"
data_use:
  - fides_key: third_party_sharing.personalized_advertising.direct_marketing
    name: Direct Marketing
    description: User information for direct marketing purposes
    recipients:
    - Processor - marketing co.
    legal_basis: Legitimate Interests
    special_category: Vital Interests
    legitimate_interest_impact_assessment: https://example.org/legitimate_interest_assessment
    parent_key: third_party_sharing.personalized_advertising
```

Replace the Data Use of `advertising` with the fides key of `third_party_sharing.personalized_advertising.direct_marketing` on our Demo Marketing System.

### Data Subject

Similarly, a Data Subject provides the opportunity to provide extra information to be used as part of the data map.

Below is our extended data subject to apply to our Demo Marketing System. Each of these properties is responsible for populating a field on your data map.

```yml title="Extended Data Subject"
data_subject:
  - fides_key: potential_customer
    name: Potential Customer
    description: A prospective individual or other organization that purchases goods or services from the organization.
    rights:
      strategy: INCLUDE
      values:
      - Informed
      - Access
      - Rectification
      - Erasure
      - Object
    automated_decisions_or_profiling: true
```

Replace the data subject of `customer` with the fides key of `potential_customer` on our Demo Marketing System.

## From Data Map to RoPA

Now that we have added the relevant information around privacy notices and data subject rights, we can export a fresh copy of our data map:

```sh title="Apply and Export Defaults"
$ fidesctl apply demo_resources/
$ fidesctl export datamap demo_resources/
```

### Additional Properties Found

Opening the new Data Map will show the previously `N/A` columns fully populated, giving us an Article 30 compliant RoPA for one of the two systems defined in `demo_resources/`. Below is a mapping of the newly populated columns with their respective properties:

* **Purpose of Processing**: The name of our newly defined extended `data_use` set in a Privacy Declaration.
* **Categories of Individuals**: The name of our newly defined extended `data_subject` set in a Privacy Declaration.
* **Categories of Recipients**: The recipients as defined in our extended Data Use.
* **Article 6 Lawful Basis for Processing Personal Data**: The `legal_basis` as defined in our extended Data Use .
* **Article 9 Condition for Processing Special Category Data**: The `special_category` as defined in our extended Data Use.
* **Legitimate Interests for the Processing**: If the `legal_basis` is `"Legitimate Interests"`, the Data Use name is used to identify what the legitimate interest data use is.
* **Link to Record of Legitimate Interests Assessment**: If the `legal_basis` is `"Legitimate Interests"`, a legitimate interests impact assessment is required and should be set using the `legitimate_interest_impact_assessment` property.
* **Rights Available to Individuals**: The `rights` as defined in our extended Data Subject based on the strategy used.
* **Existence of Automated Decision-Making, Including Profiling**: The boolean value for `automated_decisions_or_profiling` as defined in our extended Data Subject.


### Extra Credit

Follow the previous step again for the Demo Analytics System to have both systems fully compliant!


## Where to go from here?

We hope this was helpful in understanding the additional properties required for an Article 30 compliant RoPA! If there are any questions or issues you still have, we would love to hear more from you either in our [Slack Community](https://fidescommunity.slack.com) or in [an issue/PR on GitHub](https://github.com/ethyca/fides/issues).
