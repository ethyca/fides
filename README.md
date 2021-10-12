# Fides

[![Latest Version][pypi-image]][pypi-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]
[![Fides Discord Server][discord-image]][discord-url]

## :zap: Overview

Fides (*fee-dez*, Latin: Fidēs) is the modern framework for data teams to implement data privacy requirements using all your existing CI/CD tools.

- **A Privacy Grammar for engineers.** Fides is a way for you to declare when, where and how you plan to use risky types of data (e.g., personally identifiable information) directly in your code.

- **Privacy Policies that aren't just for lawyers.** Fides allows you to make a privacy policy that's *actually* enforced at time of integration and deployment.

- **CI/CD/CP.** Integrate Fides with your existing CI tool (Travis, Jenkins, Gitlab) to continuously evaluate compliance and warn users of unsafe changes _before_ they make it into production.

- **Built to scale.** Lots of databases? Tons of microservices? Large distributed infrastructure? Fides defines the data privacy taxonomy that allows for both lawyers and engineers to work together with a common language, so that the policies and rules can be applied across the entire data ecosystem.

## :bulb: Concepts

Fides has two fundamental parts at its core. The first part is the 4 privacy data types that Fides defines:

The 4 data privacy types are as follows:

- Data Category - _What_ kind of data is it?
- Data Use - _Why_ is it being used?
- Data Subject - _Whose_ data is it?
- Data Qualifier - _How_ is the data being protected?

With these privacy data types defined, subsequent resources can now be defined within their scopes. Those subsequent resources comprise the second part of Fides, they are as follows:

- Dataset - Tables and fields described as a combination of Data Categories and Data Qualifiers
- System - Defined as a list of declarations comprising all 4 privacy data types
- Policy - Defined as a list of rules comprising all 4 privacy data types, specifiying which combinations are either permitted or forbidden

Using these primitives, as well as some additional abstractions for syntactic sugar, Fides facilitates comprehensive privacy annotations for entire datascapes.

## :rocket: Quick Start

If you're looking for a more detailed introduction to Fides, we recommend following [our tutorial here](https://ethyca.github.io/fides/tutorial/). But for a quick demo you can tinker with, follow these 5 easy steps:

1. First, follow the [Getting Started with Fidesctl in Docker](https://ethyca.github.io/fides/getting_started/docker/) guide until you're able to run `fidesctl ping` successfully

    ```bash
    root@fa175a43c077:/fides/fidesctl# fidesctl ping
    Pinging http://fidesctl:8080...
    Ping Successful!
    ```

1. Run `ls demo_resources/` to inspect the contents of the demo directory, which includes some pre-made examples of the core Fides resource files (systems, datasets, policies, etc.)

    ```bash
    root@fa175a43c077:/fides/fidesctl# ls demo_resources/
    demo_dataset.yml  demo_policy.yml  demo_registry.yml  demo_system.yml
    ```

    In particular, let's look at the `demo_resources/demo_system.yml` file. It describes two basic systems: an analytics system and a marketing system, and demonstrates the basic syntax for making privacy declarations using `data_categories`, `data_uses`, `data_subjects`, and `data_qualifiers`.

    ```yaml
    system:
      - fides_key: demo_analytics_system
        name: Demo Analytics System
        description: A system used for analyzing customer behaviour.
        system_type: Service
        privacy_declarations:
          - name: Analyze customer behaviour for improvements.
            data_categories:
              - user.provided.identifiable.contact
              - user.derived.identifiable.device.cookie_id
            data_use: improve.system
            data_subjects:
              - customer
            data_qualifier: identified_data
            dataset_references:
              - demo_users_dataset

      - fides_key: demo_marketing_system
        name: Demo Marketing System
        description: Collect data about our users for marketing.
        system_type: Service
        privacy_declarations:
          - name: Collect data for marketing
            data_categories:
              #- user.provided.identifiable.contact # uncomment to add this category to the system
              - user.derived.identifiable.device.cookie_id
            data_use: advertising
            data_subjects:
              - customer
            data_qualifier: identified_data
    ```

1. Run `fidesctl evaluate demo_resources`. This will parse all the resource files, sync them to the `fidesctl` server, and then evaluate the defined policy rules to ensure all the systems are compliant:

    ```bash
    root@fa175a43c077:/fides/fidesctl# fidesctl evaluate demo_resources
    Loading resource manifests from: demo_resources
    Taxonomy successfully created.
    ----------
    Processing registry resources...
    CREATED 1 registry resources.
    UPDATED 0 registry resources.
    SKIPPED 0 registry resources.
    ----------
    Processing dataset resources...
    CREATED 1 dataset resources.
    UPDATED 0 dataset resources.
    SKIPPED 0 dataset resources.
    ----------
    Processing policy resources...
    CREATED 1 policy resources.
    UPDATED 0 policy resources.
    SKIPPED 0 policy resources.
    ----------
    Processing system resources...
    CREATED 2 system resources.
    UPDATED 0 system resources.
    SKIPPED 0 system resources.
    ----------
    Loading resource manifests from: demo_resources
    Taxonomy successfully created.
    Evaluating the following policies:
    demo_privacy_policy
    ----------
    Checking for missing resources...
    Executing evaluations...
    Sending the evaluation results to the server...
    Evaluation passed!
    ```

    Congrats, you've successfully ran your first `fidesctl evaluate` command!

1. Now, take a closer look at `demo_resources/demo_policy.yml` which describes an automated privacy policy for our demo project. This demo policy just includes one rule: reject systems that collect user provided contact information for a marketing use case.

    ```yaml
    policy:
      - fides_key: demo_privacy_policy
        name: Demo Privacy Policy
        description: The main privacy policy for the organization.
        rules:
          - fides_key: reject_direct_marketing
            name: Reject Direct Marketing
            description: Disallow collecting any user contact info to use for marketing.
            data_categories:
              inclusion: ANY
              values:
                - user.provided.identifiable.contact
            data_uses:
              inclusion: ANY
              values:
                - advertising
            data_subjects:
              inclusion: ANY
              values:
                - customer
            data_qualifier: identified_data
            action: REJECT
    ```

1. Lastly, let's modify our annotations in a way that would fail this automated privacy policy:

   - Edit `demo_resources/demo_system.yml` and uncomment the line that adds `provided_contact_information` to the list of `data_categories` for the `demo_marketing_system`

     ```diff
          privacy_declarations:
            - name: Collect data for marketing
              data_categories:
     -          #- user.provided.identifiable.contact # uncomment to add this category to the system
     +          - user.provided.identifiable.contact # uncomment to add this category to the system
                - user.derived.identifiable.device.cookie_id
              data_use: marketing_advertising_or_promotion
              data_subjects:
     ```

   - Re-run `fidesctl evaluate demo_resources` which will raise an evaluation failure!

     ```bash
     root@fa175a43c077:/fides/fidesctl# fidesctl evaluate demo_resources
     Loading resource manifests from: demo_resources
     Taxonomy successfully created.
     ----------
     Processing registry resources...
     CREATED 0 registry resources.
     UPDATED 0 registry resources.
     SKIPPED 1 registry resources.
     ----------
     Processing system resources...
     CREATED 0 system resources.
     UPDATED 1 system resources.
     SKIPPED 1 system resources.
     ----------
     Processing policy resources...
     CREATED 0 policy resources.
     UPDATED 0 policy resources.
     SKIPPED 1 policy resources.
     ----------
     Processing dataset resources...
     CREATED 0 dataset resources.
     UPDATED 0 dataset resources.
     SKIPPED 1 dataset resources.
     ----------
     Loading resource manifests from: demo_resources
     Taxonomy successfully created.
     Evaluating the following policies:
     demo_privacy_policy
     ----------
     Checking for missing resources...
     Executing evaluations...
     {
       "status": "FAIL",
       "details": [
         "Declaration (Collect data for marketing) of System (demo_marketing_system) failed Rule (Reject Direct Marketing) from Policy (demo_privacy_policy)"
       ],
       "message": null
     }
     ```

At this point, you've seen some of the core concepts in place: declaring systems, evaluating policies, and re-evaluating policies on every code change. But there's a lot more to discover, so we'd recommend following [the tutorial](https://ethyca.github.io/fides/tutorial/) to keep learning.

## :book: Learn More

Fides provides a variety of docs to help guide you to a successful outcome.

We are committed to fostering a safe and collaborative environment, such that all interactions are governed by the [Fides Code of Conduct](https://ethyca.github.io/fides/community/code_of_conduct/).

### Documentation

Full Fides documentation is available [here](https://ethyca.github.io/fides/).

### Support

Join the conversation on:

- [Discord](https://discord.gg/NfWXEmCsd4)
- [Slack](https://join.slack.com/t/fidescommunity/shared_invite/zt-vlgpv1r9-gcYrLpQyNoRf9dJu~kqE8w)
- [Twitter](https://twitter.com/ethyca)
- Discussions (TODO need to enable)

### Contributing

Read about the Fides [community](https://ethyca.github.io/fides/community/github/) or dive in to the [development guides](https://ethyca.github.io/fides/development/overview/) for information about contributions, documentation, code style, testing and more.

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
[discord-image]: https://img.shields.io/discord/730474183833813142.svg?label=&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2
[discord-url]: https://discord.gg/NfWXEmCsd4
