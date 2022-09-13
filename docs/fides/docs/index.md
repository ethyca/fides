# The Fides Ecosystem

Fides (pronounced */fee-dhez/*, from Latin: Fidēs) is an open-source privacy engineering platform for managing both the enforcement of privacy in your CI pipeline, and the fulfillment of data privacy requests in your runtime environment.

The Fides developer tools allow engineers and legal teams to label system privacy characteristics, orchestrate programmatic rights fulfillment, and audit stored personal identifiable information (PII) throughout application systems and infrastructure. This includes support for major privacy regulations (e.g. [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/)), and standards like [ISO 19944](https://www.iso.org/standard/79573.html) by default.

## Key Features
### Privacy-as-Code

Fides' extensible [description language](https://ethyca.github.io/fideslang/) allows you to describe your datasets and code in human-readable manifest files. Create a consistent, versioned definition of your system's privacy characteristics and resources for use in your [CI/CD pipeline](./cicd/examples), when processing [privacy requests](./getting-started/privacy_requests), or in the [Fides UI](./ui/overview/).

### Compliance-minded Data Mapping
Export a [data map](./guides/generate_datamaps/) of your connected databases and services, or run an [audit](./guides/generate_datamaps.md#auditing-resources/) of your resources to generate an Article 30-compliant Record of Processing Activities (RoPA). 

### Programmable Data Privacy
When your organization receives a privacy request, Fides will automatically fulfill it according to the [execution policies](./getting-started/execution_policies.md) your legal and business owners have created. Fides orchestrates connections to both your owned [databases](./guides/database_connectors.md) and [third-party systems](./saas_connectors/saas_config.md) to access, update, and delete sensitive data.

### Third-Party Integrations
Fides' core services are open source and extensible. Integrate Fides into your existing privacy compliance management tools like [OneTrust](./guides/onetrust.md) to fulfill data subject requests and return results, automatically.

### Comprehensive Privacy Standard Support

The default 'efficiently describe the privacy behaviors of your system for major regulations, including [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/) as well as major standards like [ISO 19944](https://www.iso.org/standard/79573.html).

## Why is it called Fides?

Fides was the goddess of trust and good faith in Roman paganism. Fides represented everything that was required for *"honor and credibility"* in every aspect of Roman life. In addition to this, Fides means *"reliability": reliability between two parties, which is always reciprocal*. Fides stood out for her embodiment of this project's philosophy - to provide developers with a powerful tool to make privacy a default feature of any software.

If you'd like a brief Roman mythology lesson, check out [Fides on Wikipedia](https://en.wikipedia.org/wiki/Fides_(deity)).
