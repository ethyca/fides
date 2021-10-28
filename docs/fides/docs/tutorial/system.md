# Declare your Systems

_In this section, we'll review what a system resource is, why it's needed, and how it's created and managed._

Now that we've built out the underlying databases that describe how and what type of data is stored, we're going to start grouping these into application-level "systems", another critical Fides resource.

For Best Pizza Co, you can see that they have 2 business-unit-specific applications, `Web Application` and `Analytics`:

![Best Pizza Co's Data Ecosystem](../img/BestPizzaCo_DataEcosystem.png)

At Best Pizza Co, we'll have to create a `system` resource for each of the two systems above.

## Understanding Systems
In Fides, Systems are used to model things that process data for your organization (applications, services, 3<sup>rd</sup> party APIs, etc.) and describe how these datasets are used for business functions. These dataset groupings are not mutually exclusive; they answer "_How and why are these datasets being used?_" At Best Pizza Co, you might also have a "Marketing" system and a "Financial data database" (separate from the other dbs!). The System resource groups the lowest level of data (your datasets) with your business use cases and associates qualitative attributes describing the type of data being used.

Systems use the following attributes:

| Name | Type | Description |
| --- | --- | --- |
| data_categories | List[FidesKey] | The types of sensitive data as defined by the taxonomy |
| data_subjects | List[FidesKey] | The individual persons whose data resides in your datasets |
| data_use | List[FidesKey] | The various categories of data processing and operations within your organization |
| data_qualifier | List[FidesKey] | The level of deidentification for the dataset |
| dataset_refereneces | List[FidesKey] | The `fides_key`(s) of the dataset fields used in this Privacy Declaration |

## Creating a System Resource

Let's take a look at the following system annotations for a data analytics and marketing system:

```yaml
system:
- fides_key: web_app
  name: Pizza Ordering Web Application
  description: A system used to order pizza from Best Pizza Co
  system_type: Service
  privacy_declarations:
  - name: Provide services and order tracking for customers.
    data_categories:
    - user.provided.identifiable.contact
    data_use: provide_product_or_service
    data_subjects:
    - customer
    data_qualifier: identified_data
    dataset_references:
    - appdb

- fides_key: analytics
  name: Analytics system
  description: Provide BI and insights on customer, order and inventory data
  system_type: Service
  privacy_declarations:
  - name: Collect data for business intelligence
    data_categories:
    - user.provided.identifiable.contact
    - user.derived.identifiable.device
    data_use: improve_product_or_service
    data_subjects:
    - customer
    data_qualifier: identified_data
```

The system is comprised of Privacy Declarations. These can be read colloquially as "This system uses sensitive data types of `data_categories` for `data_subjects` with the purpose of `data_use` at a deidentification level of `data_qualifier`".

You can create as many systems as are necessary to cover all of your company's business applications.

## Maintaining a System Resource

As business use cases evolve, your systems' data subjects, data categories and data uses will change with them. We recommend that updating this resource file becomes a regular part of the development planning process when building a new feature.

---

**PRO TIP**

As you add more systems to your ever-changing data ecosystem, you might want to consider grouping your systems into another Fides resource type, called a [Registry](../language/resources.md#registry).

---

## Next: Policy

With our datasets and systems in place, we've now declarated rich metadata about data privacy at Best Pizza Co. Now, we can enforce constraints on those declarations by writing [Policies](policy.md).
