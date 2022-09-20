# Glossary of Key Terms

| Term | Definition |
| --- | --- |
| [Connection](./guides/database_connectors.md) |  A configuration for how to connect a database or application to Fides. |
| [Data Category](https://ethyca.github.io/fideslang/taxonomy/data_categories/) |  *What kind of data is it?*  For example, the Data Category `user` includes things like contact email and street address. |
| [Data Qualifier](https://ethyca.github.io/fideslang/taxonomy/data_qualifiers/) | *How is the data being protected?* For example, it might be `aggregated`.
| [Data Subjects](https://ethyca.github.io/fideslang/taxonomy/data_subjects/) | *Whose data is it?* For example, a `customer`.
| [Data Uses](https://ethyca.github.io/fideslang/taxonomy/data_uses/) | *Why is it being used?*  For example, for `advertising` or to `improve` the system.
| [Dataset](https://ethyca.github.io/fideslang/resources/dataset/) | An annotation of a database schema, which describes the Collections in a database, the Fields, the Data Categories of those fields, and the relationships between relevant Collections.
| [Execution Policy](./guides/execution_policies.md) |  Different from a Policy, this is a configuration that describes what happens when a privacy request is processed. An execution policy might define that when given an email, it locates all the related data the customer has provided to you, and uploads that to a specific S3 bucket. |
| Identity | A piece of information used to uniquely identify an individual, like an email or a phone number. |
| [Identity Graph](./guides/query_execution.md) |  A mapping that knows where personal data lives, and how to look it up.  For example, you might have photos stored in a MySQL database, and customer information stored in a PostgreSQL database.  The identity graph might say to get the customer ID from the PostgreSQL database, and use that to look up the customer's photo in the MySQL database. |
| [Masking Strategy](./guides/masking_strategies.md) | How to erase or mask customer data. |
| [Pre-Webhook](./guides/policy_webhooks.md) |  Webhooks triggered on an execution policy **before** a Privacy Request is executed. |
| [Policy](./guides/policies.md) | A Policy controls what kinds of data you are permitted to commit to source code. |
| Resource | A Manifest file Fides uses to describe part of your infrastructure, written in [fideslang](https://ethyca.github.io/fideslang/).  |
| [Post-Webhook](./guides/policy_webhooks.md) | Webhooks triggered on an execution policy **after** a Privacy Request is executed. |
| [Storage](./guides/storage.md) | Where the customer's data will be sent after an access request is completed. |
| [Subject Request](./guides/privacy_requests.md) | A privacy request is a Fides representation of what is more widely known as a Data Subject Request, or Data Subject Access Request. **Access requests** are made when a customer wants to see the data an organization has collected about them. **Erasure requests** are made when a customer wants an organization to delete the data they have collected about them. |
| [System](https://ethyca.github.io/fideslang/resources/sysem/) | Systems represent the applications, services, integrations, and any software that processes data for a specific use case. |
| [Traversal](./guides/query_execution.md) | Created from an identity and an identity graph, a traversal defines how to best move through and retrieve information from your connected resources. |
| Manifest | YAML files that describe different types of objects within Fides, written in [fideslang](https://ethyca.github.io/fideslang/). |