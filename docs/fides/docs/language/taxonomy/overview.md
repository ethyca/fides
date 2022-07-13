# Fides Taxonomy

The Fides taxonomy contains four classification groups that are used together to easily describe all of the data types and associated processing behaviors of an entire tech stack; both the application and it's data storage.

## Summary of Taxonomy Classification Groups

### 1. Data Categories
Data Categories are labels to describe the type of data processed by your software. These are most heavily used by the System and Dataset resources, where you can assign one or more data categories to each field.

Data Categories are hierarchical with natural inheritance, meaning you can classify data coarsely with a high-level category (e.g. `user.provided` data), or you can classify it with greater precision using subcategories (e.g. `user.provided.identifiable.contact.email` data).

Learn more about [Data Categories in the taxonomy reference now](data_categories.md).

### 2. Data Uses
Data Uses are labels that describe how, or for what purpose(s) a component of your system is using data.

Data Uses are also hierarchical with natural inheritance, meaning you can easily describe what you're using data for either coarsely (e.g. `provide.service.operations`) or with more precision using subcategories (e.g. `provide.service.operations.support.optimization`).

Learn more about [Data Uses in the taxonomy reference now](data_uses.md).

### 3. Data Subjects
Data Subject is a label commonly used in the regulatory world to describe the users of a system who's data is being processed. In many systems a generic user label may be sufficient, however Fides language is intended to provide greater control through specificity where needed.

Examples of this are:

- `anonymous_user`
- `employee`
- `customer`
- `patient`
- `next_of_kin`

Learn more about [Data Subjects in the taxonomy reference now](data_subjects.md).


### 4. Data Qualifiers
Data Qualifiers describe the degree of identification of the given data. Think of this as a spectrum: on one end is completely anonymous data, i.e. it is impossible to identify an individual from it, and on the other end is data that specifically identifies an individual.

Along this spectrum are labels that describe the degree of identification that a given data might provide, such as:

- `identified`
- `anonymized`
- `aggregated`

Learn more about [Data Qualifiers in the taxonomy reference now](data_qualifiers.md).

### Extensibility & Interopability
The Fides language is designed to support common privacy compliance regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944.

You can extend the taxonomy to support your organization's needs. If you do this, we recommend extending from the existing categories to ensure interopability inside and outside your organization.

