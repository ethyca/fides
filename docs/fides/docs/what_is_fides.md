# What is Fides?

Fides is a tool to help you keep track of how you are working with and exposing sensitive data during the software devleopment lifecycle. By comparing your useage of sensitive data with your stated privacy policies, as well as with the data used by related systems, Fides can determine whether you are in conformance with those policies, and suggest what needs to be changed to come back into complicance.

## Components of Fides

Conceptually, there are only a few parts to Fides privacy management:

### Systems
A System is just a standalone system or software project, or really anything that has an independant lifecycle and potential useage of privacy data. As far as Fides is concerned, what matters about a system, aside from a bit of identifing data, is

- its declared useage of privacy data
- what other systems and datasets it depends on (since it may be using privacy data exposed by those other systems)

### Datasets

Similar to a system, a dataset represents the privacy exposure of a database or any other kind of data repository. Datasets are intended to allow for the description of privacy data available in a datastore.

Datastore privacy declarations differ are more limited than system privacy declarations in that datastores can't really describe or limit how data is being _used_, only what data is contained.

### Registries
A Registry is simply a collection of systems analyzed as a group. Since a registry also contains some information on how systems depend on each other, an analysis of a registry also includes checking on the validity of declared system dependencies and the validity of the declared relationships.

### Privacy Policies
Privacy policies describe what kinds of data are acceptable for use. Fides compares the data useage you are declaring against the policies you are permitting and reports on your compliance.

## How is data privacy described?

Data privacy is defined along four "axes". Each of these axes can be defined on an organization-wide basis, and allow for hierarchical definition

-  data category: What kind of data is contained here?
	 (personal health data, account data, telemetry data...)
-  data use: What is this data being used for?
 	(examples: promotion, operational support, business improvement...)
-  data subject category: What kind of person does this data refer to?
		(customer, job applicant, supplier...)
-  data qualifier: How explicitly is this data being stored?
	 	(anonymized, fully identified, aggregated...)
