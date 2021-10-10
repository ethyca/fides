# Fides (<a href="https://www.howtopronounce.com/latin/fides" target= "_blank">*fee-des*, "trust")

[![Latest Version][pypi-image]][pypi-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]



## :zap: Overview

Ethyca's Fides is a modern framework that lets legal and data teams work together to define data privacy requirements that are _provably_ enforced during software integration and deployment. By translating privacies policies into code, you can ensure that you'll never leak sensitive data in your applications.
    


- **Privacy policies that aren't just for lawyers** While your legal and executive teams define your privacy policies, it's your engineering team that must implement these policies as software. Fides defines a "privacy grammar" that lets engineers translate legal privacy policies into the language they understand: code. 

- **CI/CD** With Fides, you can update your policies and data systems as frequently as you (or your legal team!) needs. The updated policies are evaluated during the build process; if you find a potential compromise, you can shut down the process  _before_ the changes make it into production.

- **Built to scale.** Lots of databases? Tons of microservices? Large distributed infrastructure? The privacy policies that you create with Fides  can be applied across the entire data ecosystem.

## :bulb: Concepts

Your privacy policies answer the question "Can I present _this_ data to _that_ audience?" Of course, that all depends on the characteristics of the data and the audience. Fides formalizes these characteristics as four "privacy parameters":

- Data Category - What kind of data is it? A, B, C?
- Data Subject - What type of person does the data belong to? A customer? An unidentified group of users? C?
- Data Qualifier (or sensitivity|identifiability) - Is this heavily-protected PII, or anonymous 'statistical' data?
- Audience [nee Data use] - Who's going to see the data? [[marketing collateral, login screen, preferences panel}}

    


With these privacy characteristics defined, Fides lets you build a pyramid of privacy resources:

[[illo]]
    
The foundation of the pyramid comprises your datasets, lists of data categories and data qualifiers. (Examples)

Just above the datasets are your systems ...

Your datasets and systems are, in a sense, non-
    judgmental -- they simply list the possibilities of how data can be presented. But at the top of the pyramid are your policies. This is where your company's "privacy justice" is applied. A policy says "_this_ system is okay, but _that_ one? No way".
    
While every layer of the pyramid is implemented in code, the _intent_ of the policy layer is owned by your legal team (or execs, or whoever owns privacy). Given a tech-savvy lawyer, ((something something about lawyers trying code, if it's not too stupid)).
   

## :rocket: Getting Started


[[Quick Start Guide in gh-pages]]
    
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
- Re-run `fidesctl evaluate demo_resources` which will raise an evaluation failure!

    ```bash
    root@fa175a43c077:/fides/fidesctl# vim demo_resources/demo_system.yml

    root@fa175a43c077:/fides/fidesctl# git diff demo_resources/demo_system.yml
    diff --git a/fidesctl/demo_resources/demo_system.yml b/fidesctl/demo_resources/demo_system.yml
    index a707df4..e84a637 100644
    --- a/fidesctl/demo_resources/demo_system.yml
    +++ b/fidesctl/demo_resources/demo_system.yml
    @@ -24,7 +24,7 @@ system:
         privacy_declarations:
           - name: Collect data for marketing
             data_categories:
    -          #- user.provided.identifiable.contact # uncomment to add this category to the system
    +          - user.provided.identifiable.contact # uncomment to add this category to the system
               - user.derived.identifiable.device.cookie_id
             data_use: advertising
             data_subjects:

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
