# Glossary of Key Terms


## Fidesops terms

- [`Privacy Request`](guides/privacy_requests.md): A Privacy Request is a fidesops representation of what is more widely known as a Data Subject Request, or Data Subject Access Request.
    - `access` request: The customer wants to see the data an organization has collected about them.
    - `erasure` request: The customer wants an organization to delete the data they have collected about them.

- [`Policy`](guides/policies.md):  Different from a *fidesctl* Policy, this is a configuration that describes how to handle a Privacy Request. For example, you might define a simple policy that when given an email, it locates all the related data the customer has provided to you, and upload that to a specific S3 bucket.

- [`ConnectionConfig`](guides/database_connectors.md):  A configuration for how to connect a database to fidesops, so it can retrieve or remove customer data.

- [`DatasetConfig`](guides/datasets.md): A resource that contains a fidesctl Dataset (the annotation of a database schema) and its related `ConnectionConfig`

- [`StorageConfig`](guides/storage.md): A configuration for where the customer's data is going to be sent after an access request.

- [`MaskingStrategy`](guides/masking_strategies.md): A configuration for how to erase customer data - for example, you might replace a customer's email with a random string.

- `Identity`: A piece of information used to uniquely identify an individual, like an email or a phone number.

- `Identity Graph`:  A mapping that knows where personal data lives and how to look it up.  For example, you might have photos stored in a MySQL database and customer information stored in a PostgreSQL database.  The identity graph might say to get the customer id from the PostgreSQL database, and use that to look up the customer's photo in the MySQL database.

- [`Traversal`](guides/query_execution.md): Created from an identity and an identity graph. In short, it says here's the first table I'm going to visit, I'm going to get this Field, cache it, and then use that to get this information from the next Collection, and so on.

- [`PolicyPreWebhook`](guides/policy_webhooks.md): Webhooks configured on a Policy to be triggered **before** a PrivacyRequest is executed.

- [`PolicyPostWebhook`](guides/policy_webhooks.md): Webhooks configured on a Policy to be triggered **after** a PrivacyRequest is executed.

- Database terms:

    - `Datasets` - Resources at the database level. Datasets can have many Collections.
    - `Collections` - A table, or a Collection of related data. Collections can have many Fields.
    - `Fields` - Attributes on Collections.


## Fidesctl terms

See the [fidesctl repo](https://github.com/ethyca/fides) for more information, but here's some fidesctl terms that might be helpful in fidesops.

- `Manifest`: YAML files that describe different types of objects within Fides, with a high-level "privacy as code" language. 

- `Policy`: Different from a *fidesops* Policy, this controls what kinds of data you are permitted to commit to source code.  For example, you might create a fidesctl policy that says, I am not going to allow any System that takes in provided contact information and uses it for marketing purposes. 

- `Dataset`: An annotation of a database schema, which describes the Collections in a database, the Fields, the Data Categories of those fields, and the relationships between relevant Collections.

- `System`: Systems represent the applications, services, integrations, and any software that processes data for a specific use case.

- Privacy Data Types:
    - `Data Category` - *What kind of data is it?*  For example, the Data Category `user.provided.identifiable` includes things like contact email and street address.
    - `Data Use` - *Why is it being used?*  For example, for `advertising` or to `improve` the system.
    - `Data Subject` - *Whose data is it?* For example, a `customer`.
    - `Data Qualifier` - *How is the data being protected?* For example, it might be `aggregated`.