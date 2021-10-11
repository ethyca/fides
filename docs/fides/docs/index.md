# Introduction to Fides

Fides [pronounced */fee-dhez/*, from Latin: Fidēs] is an open-source privacy as code (PaC) tool by [Ethyca](https://ethyca.com) that allows you to easily declare your systems' privacy characteristics, track privacy related changes to systems & data in version control, and enforce policies in both your source code and your runtime infrastructure.

This includes support for major privacy regulations (e.g. [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/)) and standards like [ISO 19944](https://www.iso.org/standard/79573.html) by default. Fides can manage both enforcement of privacy in your CI pipeline and orchestration of data privacy requests in your runtime environment.


> *Insert video like Hashicorp - "Below, Ethyca founder and CEO, Cillian Kieran describes how Fides can help solve common privacy challenges.*

### Why is it called Fides?

Fides was the goddess of trust and good faith in Roman paganism. Fides represented everything that was required for *"honor and credibility"* in every aspect of Roman life. In addition to this, Fides means *"reliability": reliability between two parties, which is always reciprocal*.

As we considered naming conventions, Fides stood out for her embodiment of this project's philosophy - to provide developers with a powerful tool to make privacy a default feature of any software.

If you'd like a brief Roman mythology lesson, check out [Fides on Wikipedia](https://en.wikipedia.org/wiki/Fides_(deity)).


## Key Features
---

### Privacy as Code

You describe your datasets and code using Fides' high-level description language in human-readable, declarative manifest files. This allows you to create a consistent, versioned definition of privacy characteristics in your code to automate reporting, evaluate risk and execute policies against.

### Automated Privacy Checks

Fides integrates with git using the `fidestctl` tool to allow you to automate privacy checks in your CI pipeline and evalute changes against your privacy policies on each commit. This allows you to review changes and assure they meet your privacy policies before deployment.

### Support all Privacy Standards

Fides ships with a comprehensive taxonomy that allows you to efficiently describe the privacy behaviors of your system for major regulations, including [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/) as well as major standards like [ISO 19944](https://www.iso.org/standard/79573.html).

### Extensible Taxonomy

Fides taxonomy can be easily extended, allowing teams to add support for system specific concepts or data types while inheriting concepts to ensure compliance with global privacy regulations.

### Automate Privacy Reporting

Fides declarations can be configurd to automatically generate privacy review reports suitable privacy and legal team review. This allows developers to focus on implementation while providing privacy teams with greater insight into the software's privac behavior. 

### Data Privacy Rights Automation

Fides data orchestration capabilities mean you can use declarations to generate complex data rights automated processes that execute automatically against user's privacy rights requests. This allows you to easily configure automated, API driven privacy requests for access, erasure and de-identification of data.

## About Ethyca
---

### The Makers of Fides

The mission of Ethyca is to make internet scale technology respectful and ethical. We're a venture backed privacy technology team headquartered in New York, but working as a distributed team across the US to solve what we believe is the most important problem in technology today, and that is - 
 We believe the solution to this is low friction dev tools that integrate with your existing CI pipelines to make privacy a feature of your tech stack as effortlessly as any other feature of your system. Fides is a universally understandable, open source definition language on top of which we'll build privacy tools for the next decade.

### What we Believe

Data privacy is a human right that should be a native feature of any respectful technology. Today building great privacy as a feature in software is friction filled and complicated. We're building open source privacy tools for the developer community because we believe the only way to achieve a respectful internet is to make privacy an easy-to-implement layer of any tech stack.

### The Future

We've been working on this problem for three years already and have a clear view of our next five year. We're excited about the roadmap of features we'll add to Fides in order to make it comprehensive tool for addressing the major challenges of privacy in both the code management and runtime environments. This means building solutions for automated privacy analysis, as well as context rich data classification, automated data orchestration for privacy righs and semantic access control models. 
If you're interested in solving some of the toughest and most important problems facing internet scale data-driven software, [join us now](https://ethyca.com/jobs-culture/).

### Your Participation

Fides' success is predicated on your participation -- Privacy as Code can only become a reality if we ensure it's easy to understand, implement and an interopable standard for wide adoption. Your feedback, contributions and improvements are encouraged as we work towards building a community with the sole objective of building more repsectful software for everyone on the internet.


## Key Principles


## Key Features
---

### Fides Diagrams

You describe your datasets and code using Fides' high-level description language in human-readable, declarative manifest files. This allows you to create a consistent, versioned definition of privacy characteristics in your code to automate reporting, evaluate risk and execute policies against.

### Automated Privacy Checks

Fides integrates with git using the `fidesctl` tool to allow you to automate privacy checks in your CI pipeline and evalute changes against your privacy policies on each commit. This allows you to review changes and assure they meet your privacy policies before deployment.

### Support all Privacy Standards

Fides ships with a comprehensive taxonomy that allows you to efficiently describe the privacy behaviors of your system for major regulations, including [GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/), [CCPA](https://ethyca.com/cpra-hub/) and [LGPD](https://iapp.org/news/a/the-new-brazilian-general-data-protection-law-a-detailed-analysis/) as well as major standards like [ISO 19944](https://www.iso.org/standard/79573.html).

### Extensible Taxonomy

Fides' taxonomy can be easily extended, allowing teams to add support for system specific concepts or data types while inheriting concepts to ensure compliance with global privacy regulations.

### Automate Privacy Reporting

Fides' declarations can be configurd to automatically generate privacy review reports suitable privacy and legal team review. This allows developers to focus on implementation while providing privacy teams with greater insight into the software's privac behavior. 

### Data Privacy Rights Automation

Fides' data orchestration capabilities mean you can use declarations to generate complex data rights automated processes that execute automatically against user's privacy rights requests. This allows you to easily configure automated, API driven privacy requests for access, erasure and de-identification of data.

## About Ethyca
---

### The Makers of Fides

The mission of Ethyca is to make internet scale technology respectful and ethical. We're a venture backed privacy technology team headquartered in New York, but working as a distributed team across the US to solve what we believe is the most important problem in technology today, and that is - 
 We believe the solution to this is low friction dev tools that integrate with your existing CI pipelines to make privacy a feature of your tech stack as effortlessly as any other feature of your system. Fides is a universally understandable, open source definition language on top of which we'll build privacy tools for the next decade.

### What We Believe

Data privacy is a human right that should be a native feature of any respectful technology. Today building great privacy as a feature in software is friction filled and complicated. We're building open source privacy tools for the developer community because we believe the only way to achieve a respectful internet is to make privacy an easy-to-implement layer of any tech stack.

### The Future

We've been working on this problem for three years already and have a clear view of our next five year. We're excited about the roadmap of features we'll add to Fides in order to make it comprehensive tool for addressing the major challenges of privacy in both the code management and runtime environments. This means building solutions for automated privacy analysis, as well as context rich data classification, automated data orchestration for privacy righs and semantic access control models. 
If you're interested in solving some of the toughest and most important problems facing internet scale data-driven software, [join us now](https://ethyca.com/jobs-culture/).

### Your Participation

Fides' success is predicated on your participation -- Privacy as Code can only become a reality if we ensure it's easy to understand, implement and an interopable standard for wide adoption. Your feedback, contributions and improvements are encouraged as we work towards building a community with the sole objective of building more repsectful software for everyone on the internet.


## Next: Tutorial

For an in-depth tutorial, visit the [Tutorial](tutorial.md) page.
