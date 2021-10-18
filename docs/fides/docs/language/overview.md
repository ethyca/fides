# Fides Language Documentation

This is the documentation for Fides' configuration language. It is relevant to users of **Fides Control** ([`fidesctl`](https://github.com/ethyca/fides/)), **Fides Ops** ([`fidesops`](https://github.com/ethyca/fidesops/), and other privacy tools that are in the roadmap.

> **Hands-on**: Try the [fidesctl: Getting Started](../getting_started/overview.md).

The Fides language is Fides' primary user interface. In every use of Fides, configuration files written in the Fides language is always at the heart of the workflow.

## About the Fides Language

The Fides language is based on **YAML** configuration files. YAML provides a well-understood structure, upon which the Fides language adds helpful primitives which represent types of data, processes or policies. By declaring these primitives with Fides you can describe:

- what types of data your application process (using Fides `data_category` annotations)
- how your system uses that data (using Fides `data_use` annotations)
- what policies you want your system to adhere to (using Fides `Policy` resources)
- etc.

All other language features exist only to make the definition of privacy primitives more flexible and convenient.

When fully utilized, these configuration files written using the Fides language tell other Fides tools what your software is doing with data and how to manage the privacy risks of that data process. Software systems are complicated though, so a full Fides configuration will consist of multiple files describing different resources, including:

### Dataset YAML

A Dataset declaration in Fides language represents any location where data is stored: databases, data warehouses, caches and other data storage systems. Within a Fides Dataset, you declare the individual fields (e.g. database columns) where data is located and annotate them to describe the categories of data that are stored.

### System YAML

A System declaration in Fides language represents the privacy properties of a single software project, service, codebase, or application. So the Fides System declaration describes both the categories of data being processed, but also the purposes for which that data is processed.

### Policy YAML

A Policy declaration in Fides language represents a set of rules for privacy or compliance that the system must adhere to. The `fidesctl` tool evaluates these policies against the system & dataset declarations to ensure automated compliance.