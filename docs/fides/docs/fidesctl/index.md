# Fides Control

Fides Control, or *fidesctl*, is an open-source privacy-as-code (PaC) tool by [Ethyca](https://ethyca.com). Fidesctl allows you to easily declare and audit your systems' privacy characteristics, generate resource files to represent your owned infrastructure and storage, and create GDPR-compliant data maps of your organization and application.

<iframe width="560" height="315" src="https://www.youtube.com/embed/krFCQ_J_YPk" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## Key Features
### Privacy-as-Code

Describe your datasets and code in human-readable manifest files using Fides' [description language](https://ethyca.github.io/fideslang/). Create a consistent, versioned definition of your system's privacy characteristics to automate reporting, evaluate risk, and build up-to-date data maps of your business infrastructure.

### Data Map Generation
Export a data map of your connected databases and services, or run an [audit](./guides/generating_datamap.md#auditing-resources) of your [resources](https://ethyca.github.io/fideslang/resources/organization/) to generate an Article 30-compliant Record of Processing Activities (RoPA). 


### Automated Privacy Checks

The `fidesctl` tool integrates with git automate privacy checks in your CI pipeline, and evaluate changes against your privacy policies on each commit. This allows you to review changes and assure they meet your privacy policies before deployment.

### Support for all Privacy Standards

Fides ships with a comprehensive taxonomy that allows you to efficiently describe the privacy behaviors of your system for major regulations, including [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/) as well as major standards like [ISO 19944](https://www.iso.org/standard/79573.html).

### Extensible Taxonomy

Fides' taxonomy can be easily extended, allowing teams to add support in fidesctl for system specific concepts or data types while inheriting concepts to ensure compliance with global privacy regulations.

### Automate Privacy Reporting

Fidesctl' declarations can be configured to automatically generate reports suitable for privacy and legal team review. This allows developers to focus on implementation while providing privacy teams with greater insight into the software's behavior.

## Next Steps

To begin learning how Fides works, visit the [Quick Start guide](./quickstart/local_standalone.md) to walk through installation and configuration.
