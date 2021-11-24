# Annotate the System

Now that you've built out the underlying database that describes how and what type of data is stored, include the database in application-level "systems", another critical fidesctl resource.

This app contains a single Flaskr Web Application system resource. Create a `system` resource to annotate it by adding a `flaskr_system.yml` file to the `fides_resources` directory.

Writing a Fides privacy declaration requires answering the questions: _"What data is this system processing?"_, _"Why is the system processing this data?"_, _"Whose data is involved?"_, and _"How is the data protected?"_ Fides answers these questions with a `privacy_declaration` that describes the data categories, use, subjects, and qualifier. This application is quite simple, so it only has a single use: to provide the service to users. In order to do so, it requires some identifiable data (name, email, contact, etc.) and it derives some data as well (unique IDs).

For this project, the file should contain the following configuration:

```yml
system:
  - fides_key: flaskr_system
    name: Flaskr Web Application
    description: An example Flask web app that simulates an e-commerce application
    system_type: Application
    privacy_declarations:
      - name: Provide e-commerce operations to example customers
        data_categories:
          - user.provided.identifiable
          - user.derived.identifiable
          - system.operations
        data_use: provide.system.operations
        data_subjects:
          - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        dataset_references:
          - flaskr_postgres_dataset
```

Privacy Declarations can be read colloquially as "This system uses sensitive data types of `data_categories` for `data_subjects` with the purpose of `data_use` at a deidentification level of `data_qualifier`".

In a production app, create as many systems as are necessary to cover all relevant business applications.

## Understanding Systems

In fidesctl, Systems are used to model things that process data for organizations (applications, services, 3rd party APIs, etc.) and describe how these datasets are used for business functions. These groupings are not mutually exclusive; they answer "_How and why are these datasets being used?_" The System resource groups the lowest level of data (your datasets) with your business use cases, and associates qualitative attributes describing the type of data being used.

Systems use the following attributes:

| Name | Type | Description |
| --- | --- | --- |
| data_categories | List[FidesKey] | The types of sensitive data as defined by the taxonomy |
| data_subjects | List[FidesKey] | The individual persons whose data resides in your datasets |
| data_use | List[FidesKey] | The various categories of data processing and operations within your organization |
| data_qualifier | List[FidesKey] | The level of deidentification for the dataset |
| dataset_refereneces | List[FidesKey] | The `fides_key`(s) of the dataset fields used in this Privacy Declaration |

> For more detail on System resources, see the full [System resource documentation](../language/resources/system.md).

### Maintaining a System Resource

As use cases evolve, your systems' data subjects, data categories, and data uses will change as well. We recommend that updating this resource file becomes a regular part of the development planning process when building a new feature.

---

**PRO TIP**

As more systems are added to a data ecosystem, consider grouping systems into another Fides resource type, called a [Registry](../language/resources/registry.md).

---

## Next: Write a Policy

With database and system resources declared, you must now enforce your data constraints by [writing a Policy](policy.md).
