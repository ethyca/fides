# Fides

[![Latest Version][pypi-image]][pypi-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]

## :zap: Overview

Fides (*fee-dez*, Latin: Fidēs) is the modern framework for data teams to implement data privacy requirements using all your existing CI/CD tools.

- **A Privacy Grammar for Engineers.** Fides is a way for you to declare when, where and how you plan to use risky types of data (e.g. personally identifiable information) directly in your code.

- **Privacy Policies That Aren't Just for Lawyers.** Fides allows you to make a privacy policy that's *actually* enforced at time of integration and deployment.

- **CI/CD/CP.** Update your policies and data systems as frequently as you (or your legal team!) needs. The updated policies will continuously evaluate compliance and warn users of unsafe changes _before_ they make it into production.

- **Built to Scale.** Lots of databases? Tons of microservices? Large distributed infrastructure? Fides defines the data privacy taxonomy that allows for both lawyers and engineers to work together with a common language, so that the policies and rules can be applied across the entire data ecosystem.

## :bulb: Concepts

Fides has two fundamental pieces at its core. The first is the 4 data privacy types, and the second is the resources that are defined and described in terms of their data privacy type composition.

The 4 data privacy types are as follows:

- Data Categories - _What_ kind of data is it?
- Data Subjects - _Who's_ data is it?
- Data Uses - _How_ is it being used?
- Data Qualifiers - How _identifiable_ is it?

With the data privacy types defined, additional resources can now be defined within their context, for instance:

- Dataset - Defined as a combination of Data Categories and Data Qualifiers
- System - Defined as a list of declarations comprising all 4 data privacy types
- Policy - Defined as a list of rules comprising all 4 data privacy types, specifiying which combinations are either permitted or forbidden

Using these primitives as well as some addiitional abstractions for syntactic sugar, Fides facilitates comprehensive privacy annotations for entire datascapes.

## :rocket: Getting Started

We recommend getting started with [our tutorial here](https://github.com/ethyca/fides/blob/main/docs/fides/docs/tutorial.md), but it's simple to jump right in with 5 easy steps:

1. Install Fides via pip:

    ```bash
    pip install fidesctl
    ```

1. Create a directory for your Fides resources to live in, like `fides_resources/`.

    ```bash
    mkdir fides_resources/
    ```

1. Let's make our first policy, you don't even need a lawyer :wink: using our template, modify and add what ever rules you'd like

    <details>
    <summary>Here's an example policy .yaml to get you started</summary>

      ```yaml
    policy:
      - organizationId: 1
        fidesKey: "primary_privacy_policy"
        name: "Primary Privacy Policy"
        description: "The main privacy policy for the organization."
        rules:
          - organizationId: 1
            fidesKey: "reject_targeted_marketing"
            name: "Reject Targeted Marketing"
            description: "Disallow marketing that is targeted towards users."
            dataCategories:
              inclusion: "ANY"
              values:
                - profiling_data
                - account_data
                - derived_data
                - cloud_service_provider_data
            dataUses:
              inclusion: ANY
              values:
                - market_advertise_or_promote
                - offer_upgrades_or_upsell
            dataSubjects:
              inclusion: ANY
              values:
                - trainee
                - commuter
            dataQualifier: pseudonymized_data
            action: REJECT
          - organizationId: 1
            fidesKey: "reject_some_marketing"
            name: "Reject Some Marketing"
            description: "Disallow some marketing that is targeted towards users."
            dataCategories:
              inclusion: ANY
              values:
                - user_location
                - personal_health_data_and_medical_records
                - connectivity_data
                - credentials
            dataUses:
              inclusion: ALL
              values:
                - improvement_of_business_support_for_contracted_service
                - personalize
                - share_when_required_to_provide_the_service
            dataSubjects:
              inclusion: NONE
              values:
                - trainee
                - commuter
                - patient
            dataQualifier: pseudonymized_data
            action: REJECT
      ```

    </details>

1. And now, create a data system for Fides to check your data privacy policy against.

    <details>
        <summary>Here's an example system .yaml to get you started</summary>

      ```yaml
    system:
      - organizationId: 1
        fidesKey: "demo_system"
        name: "Demo System"
        description: "A system used for demos."
        systemType: "Service"
        privacyDeclarations:
          - name: "Analyze Anonymous Content"
            dataCategories:
              - "account_data"
            dataUse: "provide"
            dataQualifier: "anonymized_data"
            dataSubjects:
              - "anonymous_user"
            datasetReferences:
              - "sample_db_dataset.Email"
        systemDependencies:
          - user_service
      ```

    </details>

1. Send all your resources to the server using `fidesctl apply fides_manifests/` and that's it! See how your data set stacks up against the policy by using `fidesctl evaluate`

And ICYMI, we really recommend doing [the tutorial](https://github.com/ethyca/fides/blob/main/docs/fides/docs/tutorial.md). It's helpful to contextualize how you can use Fides in your organization, today!

## :book: Resources

Fides provides a variety of resources to help guide you to a successful outcome.

We are commmitted to fostering a safe and collaborative environment, such that all interactions are governed by the [Fides Code of Conduct](https://github.com/ethyca/fides/tree/main/docs/fides/docs/community/code_of_conduct.md).

### Documentation

Full Fides documentation is available [here](https://github.com/ethyca/fides/tree/main/docs/fides/docs).

### Contributing

Read about the Fides [community](https://github.com/ethyca/fides/tree/main/docs/fides/docs/community) or dive in to the [development guides](https://github.com/ethyca/fides/blob/main/docs/fides/docs/development/overview.md) for information about contributions, documentation, code style, testing and more.

## Installation

### Requirements

Fides requires Python 3.8+. If you're new to Python, we recommend installing the [Anaconda distribution](https://www.anaconda.com/products/individual).

### Latest Release

To install Fides, run:

```bash
pip install fidesctl
```

### Bleeding Edge

For development or just to try out the latest features, you may want to install Fides directly from source.

Please note that the main branch of Fides is not guaranteed to be stable, and is not suitable for production environments.

```bash
git clone https://github.com/ethyca/fides.git
pip install -e .
```

## License

Fides is licensed under the [Apache Software License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

[pypi-image]: https://img.shields.io/pypi/v/fidesctl.svg
[pypi-url]: https://pypi.python.org/pypi/fidesctl/
[license-image]: https://img.shields.io/:license-Apache%202-blue.svg
[license-url]: https://www.apache.org/licenses/LICENSE-2.0.txt
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black/
[mypy-image]: http://www.mypy-lang.org/static/mypy_badge.svg
[mypy-url]: http://mypy-lang.org/
