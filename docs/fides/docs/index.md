# Introduction to Fides

Fides [pronounced */fee-dhez/*, from Latin: Fidēs] is an open-source privacy as code (PaC) tool by [Ethyca](https://ethyca.com) that allows you to easily declare your systems' privacy characteristics, track privacy related changes to systems & data in version control, and enforce policies in both your source code and your runtime infrastructure.

This includes support for major privacy regulations (e.g. [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/)) and standards like [ISO 19944](https://www.iso.org/standard/79573.html) by default. Fides can manage both enforcement of privacy in your CI pipeline and orchestration of data privacy requests in your runtime environment.

<iframe width="560" height="315" src="https://www.youtube.com/embed/WdJCTz0wi_Q" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

### Why is it called Fides?

Fides was the goddess of trust and good faith in Roman paganism. Fides represented everything that was required for *"honor and credibility"* in every aspect of Roman life. In addition to this, Fides means *"reliability": reliability between two parties, which is always reciprocal*.

As we considered naming conventions, Fides stood out for her embodiment of this project's philosophy - to provide developers with a powerful tool to make privacy a default feature of any software.

If you'd like a brief Roman mythology lesson, check out [Fides on Wikipedia](https://en.wikipedia.org/wiki/Fides_(deity)).


## Key Features
---

### Privacy as Code

You describe your datasets and code using Fides' high-level description language in human-readable, declarative manifest files. This allows you to create a consistent, versioned definition of privacy characteristics in your code to automate reporting, evaluate risk and execute policies against.

### Automated Privacy Checks

Fides integrates with git using the `fidesctl` tool to allow you to automate privacy checks in your CI pipeline and evalute changes against your privacy policies on each commit. This allows you to review changes and assure they meet your privacy policies before deployment.

### Support all Privacy Standards

Fides ships with a comprehensive taxonomy that allows you to efficiently describe the privacy behaviors of your system for major regulations, including [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/) as well as major standards like [ISO 19944](https://www.iso.org/standard/79573.html).

### Extensible Taxonomy

Fides' taxonomy can be easily extended, allowing teams to add support for system specific concepts or data types while inheriting concepts to ensure compliance with global privacy regulations.

### Automate Privacy Reporting

Fides' declarations can be configurd to automatically generate privacy review reports suitable for privacy and legal team review. This allows developers to focus on implementation while providing privacy teams with greater insight into the software's behavior.

### Data Privacy Rights Automation

Fides' data orchestration capabilities mean you can use declarations to generate complex data rights automated processes that execute automatically against user's privacy rights requests. This allows you to easily configure automated, API driven privacy requests for access, erasure and de-identification of data.

## Next Steps

To start learning how Fides works, visit the [Tutorial](tutorial/overview.md) page to walkthrough using the taxonomy, annotating datasets and systems, writing and evaluating policies, and more. Welcome!
