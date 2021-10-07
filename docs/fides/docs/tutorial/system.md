# Creating Systems
_In this section, we'll review what a system resource is, why it's needed, and how it's created and managed._

Now that we've built out the underlying databases that describe how the data is stored and what type of data is there, we're going to start grouping these into application-level "systems", another critical Fides resource. 

## Understanding Systems
Systems describe how these datasets are used for business functions around your organization. These dataset groupings are not mutually exclusive and answer the questions of "_How and why are these datasets being used?_"

Systems use the following attributes: 

| Name | Type | Description |
|  --- | --- | --- |
| data_categories | List[FidesKey] | The data categories, or types of sensitive data as defined in the taxonomy |
| data_subjects | List[FidesKey] | The data subjects, or individual persons whose data resides in your datasets |
| data_use | List[FidesKey] | Data use describes the various categories of data processing and operations at your organization |
| data_qualifier | List[FidesKey] | Data qualifier describes the level of deidentification for the dataset |
| dataset_refereneces | List[FidesKey] | The fides_key(s) of the dataset fields used in this Privacy Declaration. |

As you can see, the System resource groups the lowest level of data (your datasets) with your business use cases and associates qualitative attributes describing what type of data is being used. 

## Creating a System Resource
Let's take a look at the following system annotations for a data analytics and marketing system:

```yaml
  system:
    - fides_key: data_analytics_system
      name: Data Analytics System
      description: A system used to extract insights about customer behavior in our app.
      system_type: Service
      privacy_declarations:
        - name: Analyze customer behavior for improvements.
          data_categories:
            - user.provided.identifiable.contact
            - user.derived.identifiable.device.cookie_id
          data_use: improve_product_or_service
          data_subjects:
            - customer
          data_qualifier: identified_data
          dataset_references:
            - appdb

    - fides_key: marketing_system
      name: Marketing System
      description: Collect data about our users for marketing.
      system_type: Service
      privacy_declarations:
        - name: Collect data for marketing
          data_categories:
            - user.provided.identifiable.contact
            - user.derived.identifiable.device.cookie_id
          data_use: marketing_advertising_or_promotion
          data_subjects:
            - customer
          data_qualifier: identified_data
```

As you can see, the system is comprised of Privacy Declarations. These can be read colloquially as "This system uses sensitive data types of `data_categories` for `data_subjects` with the purpose of `data_use` at a deidentification level of `data_qualifier`". 

You can create as many systems you'd like to cover all of your company's business applications. 

## Maintaining a System Resource
As business use cases evolve, your systems' data subjects, data categories and data uses will change with them. We recommend that updating this resource file become a regular part of the development planning process when building a new feature. 

As you add more systems to your ever-changing data ecosystem, you might want to consider grouping your systems into another Fides resource type, called a "Registry". This is just a logical grouping of Systems. 