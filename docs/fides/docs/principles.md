## Key Principles

* Data lineage declarations
* Privacy controls at the CI layer
* Predefined privacy taxonomy
* Translation layer between engineers and lawyers

---

### Fides Diagrams

### Applying Manifests

![alt text](img/Manifest_Flow.svg "Fides Manifest Workflow")

### CI Checks

![alt text](img/CI_Workflow.svg "Fides CI Workflow")

---

## Core Components

Conceptually, there are a few key parts to Fides privacy management. For more in-depth info on each resource and their respective schemas, see the [Fides Resources](fides_resources.md) page.

### Systems

A System is a standalone application, software project, service, etc. that has an independent lifecycle and potential usage of privacy data. As far as Fides is concerned, the important parts of a system are:

* Its declared usage of privacy data
* What other systems it depends on, since those other systems may also use privacy data

### Datasets

Similar to a system, a dataset represents the privacy exposure of a database, datastore, or any other kind of data repository. Datasets are intended to allow for the description of privacy data within said repository.

Datastore privacy declarations are more limited than system privacy declarations in that they only accept Data Categories and Data Qualifiers.

Datasets are annotated on a per-field basis.

### Registries

A Registry is a collection of systems evaluated as a group. Since a registry contains information on how systems depend on each other, an analysis of a registry also includes checking on the validity of each system and their dependencies.

### Privacy Policies

Privacy Policies describe what kinds of data are acceptable for what kinds of use. Fides compares the data usage you are declaring against the policies you are defining to evaluate your state of compliance.

### Describing Data Privacy

Fides defines data privacy in four dimensions, called Data Privacy Classifiers. Each of these classifiers can be defined on an organization-wide basis, and allow for hierarchical definition:

* Data category: What kind of data is contained here?
(personal health data, account data, telemetry data...)
* Data use: What is this data being used for?
(examples: promotion, operational support, business improvement...)
* Data subject category: What kind of person does this data refer to?
(customer, job applicant, supplier...)
* Data qualifier: How explicitly is this data being stored?
(anonymized, fully identified, aggregated...)