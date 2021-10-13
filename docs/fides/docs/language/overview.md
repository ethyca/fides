# Fides Language Documentation

This is the documentation for Fides' configuration language. It is relevant to users of **Fides Control** `fidesctl`, **Fides Ops** `fidesops` and other privacy tools that are in the roadmap.

> **Hands-on**: Try the [Fides: Getting Started](../getting_started/overview.md).

The Fides language is Fides' primary user interface. In every use of Fides, a configuration written in the Fides language is always at the heart of the workflow.

## About the Fides Language

The Fides language is based on **YAML** configuration files. The main purpose of the Fides language is declaring primitives, which represent types of data, processes or policies. By declaring these primitives with Fides you can describe:

- what types of data your application process,
- how your system uses that data
- what policies you want your system to adhere to. 

All other language features exist only to make the definition of privacy primitives more flexible and convenient.

A Fides configuration is a complete document in the Fides language that tells Fides what you're doing with data and how to manage the privacy risks of that data process. A Fides configuration can consist of multiple files and directories but typically requires the following resources:

### Dataset YAML

A Dataset declaration in Fides language represents any system in which data is stored - Dataset declarations are used to describe the types of data in databases, data warehouses, caches and other data storage systems.

### System YAML

A system declaration in Fides language represents the privacy properties of a single software project, service, codebase, or application. So the system declaration describes the types of data and purposes for which that data is processed.

### Policy YAML

A Policy declaration in Fides language represents a set of rules for privacy or compliance that the system must adhere to. These policies reside in Fides Control server. Dataset and System declarations are evaluated against Policies by Fides.