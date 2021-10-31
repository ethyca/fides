# What is Fidesops?

Fidesops (fee-dez-äps, combination of the Latin term "Fidēs" + "operations") is an open-source, extensible, deployed engine that fulfills any privacy request (e.g. access request, erasure request) by connecting directly to your disparate databases.

## Programmable Data Privacy
Fidesops connects and orchestrates calls to all of your databases in order to access, update and delete sensitive data per your policy configuration written in [Fideslang](https://github.com/ethyca/privacy-taxonomy).

## DAGs for Datastores
Fidesops works by integrating all your data store connections into a unified graph - also known as a DAG. We know that sensitive data is stored all around your dynamic ecosystem, so Fidesops builds the DAG at runtime.

## B.Y.O. DSAR Automation Provider
Fidesops handles the integration to your existing privacy management tools like OneTrust to fulfill Data Subject Requests and return the package back to the DSAR Automation provider.

## Built to Scale
Lots of databases? Tons of microservices? Connect as many databases and services as you'd like, and let Fidesops do the heavy lifting (like auth management, failure retry, and error handling).

# How does Fidesops work with Fidesctl and Fideslang?
In a software organization, the team that writes and delivers software is normally the same team responsible for executing a privacy request when it comes in from customer support or legal because you know where the data lives.  When your organization receives a privacy request, Fideops will automatically fulfill a privacy request per the execution policies your legal and business owners have created by querying your databases directly. 

![Fidesops business process](img/fides-ops-process.png "Fidesops biz process")

Your policies and database annotations are written in [**Fideslang**](https://github.com/ethyca/privacy-taxonomy): the syntax that describes the attributes of your data and its allowed purposes of use. 

But after identifying what types of data are in your databases using Fideslang, how will your organization know what data is deemed sensitive? And how will your orgnaization prevent inappropriate uses of that data? That's where [**Fidesctl**](https://github.com/ethyca/fides) comes in. 

![Fides ecosystem](img/fides-ecosystem.png "Fides ecosystem")

Fidesctl is a CLI tool that continuously verifies Fideslang database annotations against acceptable use privacy policies.