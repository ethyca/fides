# Annotate the Fidesctl Resources

Making the Fidesctl tools available within the app's virtual environment is just the beginning. Next, configure Fidesctl for this app by annotating its resources using manifest files.

First, create a `fides_resources` directory at the project root. This is where the manifest files will be stored.

  > **Note:** In a production app this directory can have any name, but it's a best practice to create a specific directory to house the Fidesctl manifest files.

## Annotate the Dataset

Fundamentally, the data ecosystem is built on data that is stored _somewhere_. In Fidesctl, Datasets are used for granular, field-level annotations of exactly what data your systems are storing and where that data is stored. For example, an app might declare one dataset for a Postgres application database, a second dataset for a Mongo orders collection, and a third dataset for some CSV files in cloud storage. The Dataset resource provides a database-agnostic way to annotate the fields stored in these systems with Data Categories, providing a metadata layer that other tooling can consume.

This app contains a single PostgreSQL dataset. Create a `dataset` resource to annotate it by adding a `flaskr_postgres_dataset.yml` file to the `fides_resources` directory. This file should contain the following configuration:

```yml
dataset:
- fides_key: flaskr_postgres_dataset
  name: Flaskr Example PostgreSQL Database
  description: Application database for Flaskr example app
  collections:
  - name: products
    fields:
    - name: created_at
      data_categories: [system.operations]
    - name: description
      data_categories: [user.provided.identifiable]
    - name: id
      data_categories: [system.operations]
    - name: name
      data_categories: [user.provided.identifiable]
    - name: price
      data_categories: [user.provided.identifiable]
    - name: seller_id
      data_categories: [user.derived.identifiable.unique_id]
  - name: purchases
    fields:
    - name: buyer_id
      data_categories: [user.derived.identifiable.unique_id]
    - name: city
      data_categories: [user.provided.identifiable.contact.city]
    - name: created_at
      data_categories: [system.operations]
    - name: id
      data_categories: [system.operations]
    - name: product_id
      data_categories: [system.operations]
    - name: state
      data_categories: [user.provided.identifiable.contact.state]
    - name: street_1
      data_categories: [user.provided.identifiable.contact.street]
    - name: street_2
      data_categories: [user.provided.identifiable.contact.street]
    - name: zip
      data_categories: [user.provided.identifiable.contact.postal_code]
  - name: users
    fields:
    - name: created_at
      data_categories: [system.operations]
    - name: email
      data_categories: [user.provided.identifiable.contact.email]
    - name: first_name
      data_categories: [user.provided.identifiable.name]
    - name: id
      data_categories: [user.derived.identifiable.unique_id]
    - name: last_name
      data_categories: [user.provided.identifiable.name]
    - name: password
      data_categories: [user.provided.identifiable.credentials.password]
      data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized
```

<!-- TODO: Link to the `generate-dataset` usage documentation below, when it exists. -->

As an alternative to manually authoring the resource file, you can also use the `generate-dataset` CLI command. The CLI will connect to the database and automatically generate a non-annotated resource YAML file in the specified location, based on the database schema. For this project, the command is:

```sh
./venv/bin/fidesctl generate-dataset \
postgresql://postgres:postgres@localhost:5432/flaskr \
fides_resources/flaskr_postgres_dataset.yml
```

### Understanding the Dataset Resource

This YAML serves as the foundation of `fideslang`, the Fides language; it answers "_What data and kinds of data do we have?_" and "_How is our data organized?_". The language is built on declaring the types of data found in storage for your organization.

In traditional SQL, Fidesctl defines the following:
- "datasets" as database schemas
- "collections" as database tables
- "fields" as database columns

For NoSQL datasets, Fidesctl defines the following:
- "dataset"
- "collection" as a logical grouping of data fields (ie: in MongoDB, this is called a "Collection")
- "fields" as a reference to an individual data element (ie: in MongoDB, this is called a "field")

Additionally, `fideslang` has attributes that describe what kind of data is contained in this dataset. We use the following attributes to describe the data:

| Name | Type | Description |
| --- | --- | --- |
| name | String | The name of this field |
| description | String | A description of what this field contains |
| data_categories | List[FidesKey] | The types of sensitive data, as defined by the taxonomy, that can be found in this field |
| data_qualifier | FidesKey | The level of deidentification for the dataset |

---

**PRO TIP**

As you're progressing with the tutorial, we recommend installing our [FidesCTL VS Code extension](https://marketplace.visualstudio.com/items?itemName=ethyca.fidesctl), which will validate the syntax in real-time as you're writing your resource files!

---

### Maintaining a Dataset Resource

As apps add more databases and other services to store potentially sensitive data, it is recommended that updating this resource file becomes a part of the development process when building a new feature.

## Annotate the System

Now that you've built out the underlying database that describes how and what type of data is stored, include the database in application-level "systems", another critical Fidesctl resource.

This app contains a single Flaskr Web Application system resource. Create a `system` resource to annotate it by adding a `flaskr_system.yml` file to the `fides_resources` directory. This file should contain the following configuration:

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

The system is comprised of Privacy Declarations. These can be read colloquially as "This system uses sensitive data types of `data_categories` for `data_subjects` with the purpose of `data_use` at a deidentification level of `data_qualifier`".

In a production app, create as many systems as are necessary to cover all relevant business applications.

### Understanding Systems

In Fidesctl, Systems are used to model things that process data for organizations (applications, services, 3<sup>rd</sup> party APIs, etc.) and describe how these datasets are used for business functions. These groupings are not mutually exclusive; they answer "_How and why are these datasets being used?_" The System resource groups the lowest level of data (your datasets) with your business use cases, and associates qualitative attributes describing the type of data being used.

Systems use the following attributes:

| Name | Type | Description |
| --- | --- | --- |
| data_categories | List[FidesKey] | The types of sensitive data as defined by the taxonomy |
| data_subjects | List[FidesKey] | The individual persons whose data resides in your datasets |
| data_use | List[FidesKey] | The various categories of data processing and operations within your organization |
| data_qualifier | List[FidesKey] | The level of deidentification for the dataset |
| dataset_refereneces | List[FidesKey] | The `fides_key`(s) of the dataset fields used in this Privacy Declaration |

### Maintaining a System Resource

As use cases evolve, your systems' data subjects, data categories, and data uses will change as well. We recommend that updating this resource file becomes a regular part of the development planning process when building a new feature.

---

**PRO TIP**

As more systems are added to a data ecosystem, consider grouping systems into another Fides resource type, called a [Registry](../language/resources.md#registry).

---

## Annotate the Policy

Fidesctl's privacy declarations provide rich metadata about systems, the data categories they process, and the uses of that data. Policies allow you to enforce constraints on these declarations and decide what combinations to allow or reject at your company, thus providing a layer of automation to control data privacy at the source.

Define a single Policy by creating a `flaskr_policy.yml` file in the `fides_resources` directory. This file should contain the following configuration:

```yml
policy:
  - fides_key: flaskr_policy
    name: Flaskr Privacy Policy
    description: A privacy policy for the example Flask app
    rules:
      - fides_key: minimize_user_identifiable_data
        name: Minimize User Identifiable Data
        description: Reject collecting any user identifiable data for uses other than system operations
        data_categories:
          inclusion: ANY
          values:
            - user.provided.identifiable
            - user.derived.identifiable
        data_uses:
          inclusion: ANY
          values:
            - improve
            - personalize
            - advertising
            - third_party_sharing
            - collect
            - train_ai_system
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        action: REJECT

      - fides_key: reject_sensitive_data
        name: Reject Sensitive Data
        description: Reject collecting sensitive user data for any use
        data_categories:
          inclusion: ANY
          values:
            - user.provided.identifiable.biometric
            - user.provided.identifiable.childrens
            - user.provided.identifiable.genetic
            - user.provided.identifiable.health_and_medical
            - user.provided.identifiable.political_opinion
            - user.provided.identifiable.race
            - user.provided.identifiable.religious_belief
            - user.provided.identifiable.sexual_orientation
        data_uses:
          inclusion: ANY
          values:
            - provide
            - improve
            - personalize
            - advertising
            - third_party_sharing
            - collect
            - train_ai_system
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated
        action: REJECT
```

### Understanding the policy

The purpose of a privacy policy is to state what types of data are allowed for certain means of use. In Fidesctl, a Policy is comprised of rules against which the system's privacy declarations are evaluated. Policies will evaluate the data subjects, data category, and data qualifier values against data use cases. This generates a boolean output to either allow or reject the process from proceeding.

Policies use the following attributes:

| Name | Type | Description |
| --- | --- | --- |
| fides_key | FidesKey | An identifier label that must be unique within your organization. A fides_key can only contain alphanumeric characters and `_`. |
| data_categories | List[DataRule] | The types of sensitive data as defined by the taxonomy |
| data_uses | List[DataRule] | The various categories of data processing and operations within your organization |
| data_subjects | List[DataRule] | The individual persons to whom you data rule pertains |
| data_qualifier | String | The acceptable or non-acceptable level of deidentification |
| action | Choice | A string, either `ACCEPT` or `REJECT` |

### Maintaining a Policy

As global privacy laws change and businesses scale, a company's policies will evolve with them. We recommend that updating this resource file becomes a regular part of the development planning process when building a new feature.

## Check Your Progress

After making the above changes, your app should resemble the state of the [`ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) at the [`fidesctl-manifests`](https://github.com/ethyca/fidesdemo/releases/tag/fidesctl-manifests) tag.

## Next: Add Google Analytics

Improve usage telemetry for this project by adding the nefarious tracker, [Google Analytics](google.md).
