# Meet Fidesctl: Privacy Policies as Code

[![Latest Release Version][release-image]][release-url]
[![Docker][docker-workflow-image]][docker-actions-url]
[![Docs][docs-workflow-image]][docs-actions-url]
[![Package][release-workflow-image]][publish-actions-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]
[![Twitter][twitter-image]][twitter-url]


![Fidesctl banner](docs/fides/docs/img/fidesctl.png "Fidesctl banner")

 _[Join the waitlist](https://ethyca.com/waitlist/) to get started with our free, hosted version!_

## :zap: Overview

Fides (*fee-dhez*, Latin: Fidēs) is an open-source tool that allows you to easily [declare your systems' privacy characteristics](https://ethyca.github.io/fides/tutorial/system/), [track privacy related changes](https://ethyca.github.io/fides/tutorial/policy/) to systems and data in version control, and [enforce policies](https://ethyca.github.io/fides/tutorial/pass/#evaluate-the-fidesctl-policies) in both your source code and [your runtime infrastructure](https://ethyca.github.io/fides/deployment/#step-5-install-fidesctl-cli-on-ci-build-server).

![Fidesctl overview](docs/fides/docs/img/fidesctl-overview-diagram.png "Fidesctl overview")

## :rocket: Quick Start

1. Get running with Docker: First, ensure that you have `make` and `docker` installed locally, and clone the Fides repo. Then, from the fides directory, run the following commands:

    <details>

    This will spin up the entire project and open a shell within the `fidesctl` container. Once you see the `fidesctl#` prompt (takes ~3 minutes the first time), you know you're ready to go:

    <summary>Run <code>make cli</code></summary>

      ```bash
      ~/git/fides% make cli
      Build the images required in the docker-compose file...
      ...
      Building fidesapi
      ...
      Building fidesctl
      ...
      Building docs
      ...
      root@1a742083cedf:/fides/fidesctl#
      ```

    </details>

    <details>
    This builds the required images, spins up the database, and runs the initialization scripts.

    <summary>Run <code>fidesctl init</code></summary>

    ```
    Initializing Fidesctl...
    ----------
    Created a './.fides' directory.
    ----------
    Created a fidesctl config file: ./.fides/fidesctl.toml
    To learn more about configuring fidesctl, see:
      https://ethyca.github.io/fides/installation/configuration/
    ----------
    For example policies and help getting started, see:
      https://ethyca.github.io/fides/guides/policies/
    ----------
    Fidesctl initialization complete.
    ```

    </details>


2. Use the <code>evaluate</code> command to see if this project's demo analytics and demo marketing systems are compliant with your privacy policy as code:
    <details>

    <summary>Run <code>fidesctl evaluate demo_resources/</code></summary>

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

    </details>

    Congratulations, you've successfully run your first fidesctl `evaluate` command!

3. Now, take a closer look at `demo_resources/demo_policy.yml` which describes an organization's privacy policy as code. This policy just includes one rule: fail if any system uses contact information for marketing purposes.
    <details>
      <summary>Run <code>cat demo_resources/demo_policy.yml</code></summary>

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
                matches: ANY
                values:
                  - user.provided.identifiable.contact
              data_uses:
                matches: ANY
                values:
                  - advertising
              data_subjects:
                matches: ANY
                values:
                  - customer
              data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
      ```

      </details>


4. Lastly, we're going to modify our annotations in a way that would fail the policy we just looked at:
    <details>

    Edit `demo_resources/demo_system.yml` and uncomment the line that adds `user.provided.identifiable.contact` to the list of `data_categories` for the `demo_marketing_system`.
      <summary>Add User-provided contact info to the demo_marketing_system</summary>

     ```diff
          privacy_declarations:
            - name: Collect data for marketing
              data_categories:
     -          #- user.provided.identifiable.contact # uncomment to add this category to the system
     +          - user.provided.identifiable.contact # uncomment to add this category to the system
                - user.derived.identifiable.device.cookie_id
              data_uses: marketing_advertising_or_promotion
              data_subjects:
     ```

     </details>

    <details>

      <summary>Run <code>fidesctl evaluate demo_resources/</code> </summary>

      Running `fidesctl evaluate demo_resources` now causes an evaluation failure. The privacy policy "Reject Direct Marketing" rule disallows collecting contact information for marketing purposes, and flagged the violating `privacy_declaration` during evaluation.

     ```bash
     root@fa175a43c077:/fides/fidesctl# fidesctl evaluate demo_resources
     ...
     Executing evaluations...
     {
       "status": "FAIL",
       "details": [
         "Declaration (Collect data for marketing) of System (demo_marketing_system) failed Rule (Reject Direct Marketing) from Policy (demo_privacy_policy)"
       ],
       "message": null
     }
     ```

    </details>

At this point, you've seen some of the core concepts in place: declaring systems, evaluating policies, and re-evaluating policies on every code change. But there's a lot more to discover, so we'd recommend following [the tutorial](https://ethyca.github.io/fides/tutorial/) to keep learning.

## :book: Learn More

The Fides core team is committed to providing a variety of documentation to help get you started using Fidesctl.  As such, all interactions are governed by the [Fides Code of Conduct](https://ethyca.github.io/fides/community/code_of_conduct/).

### Documentation

For more information on getting started with Fides, how to configure and set up Fides, and more about the Fides ecosystem of open source projects:

- Documentation: https://ethyca.github.io/fides/
- Tutorial: https://ethyca.github.io/fides/tutorial/
- Deployment: https://ethyca.github.io/fides/deployment/
- Roadmap: https://github.com/ethyca/fides/projects
- Website: www.ethyca.com/fides

### Support

Join the conversation on:

- [Slack](https://fid.es/join-slack)
- [Twitter](https://twitter.com/ethyca)
- [Discussions](https://github.com/ethyca/fides/discussions)

### Contributing

We welcome and encourage all types of contributions and improvements!  Please see our [contribution guide](https://ethyca.github.io/fides/development/overview/) to opening issues for bugs, new features, and security or experience enhancements.

Read about the [Fides community](https://ethyca.github.io/fides/community/hints_tips/) or dive into the [development guides](https://ethyca.github.io/fides/development/overview) for information about contributions, documentation, code style, testing and more. Ethyca is committed to fostering a safe and collaborative environment, such that all interactions are governed by the [Fides Code of Conduct](https://ethyca.github.io/fides/community/code_of_conduct/).

## :balance_scale: License

The Fides ecosystem of tools ([Fidesops](https://github.com/ethyca/fidesops) and [Fidesctl](https://github.com/ethyca/fides)) are licensed under the [Apache Software License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
Fides tools are built on [Fideslang](https://github.com/ethyca/privacy-taxonomy), the Fides language specification, which is licensed under [CC by 4](https://github.com/ethyca/privacy-taxonomy/blob/main/LICENSE).

Fides is created and sponsored by Ethyca: a developer tools company building the trust infrastructure of the internet. If you have questions or need assistance getting started, let us know at fides@ethyca.com!

[release-image]: https://img.shields.io/github/release/ethyca/fides.svg
[release-url]: https://github.com/ethyca/fides/releases
[docker-workflow-image]: https://github.com/ethyca/fides/workflows/Docker%20Build%20&%20Push/badge.svg
[docs-workflow-image]: https://github.com/ethyca/fides/workflows/Publish%20Docs/badge.svg
[release-workflow-image]: https://github.com/ethyca/fides/workflows/Publish%20fidesctl/badge.svg
[docker-actions-url]: https://github.com/ethyca/fides/actions/workflows/docker.yaml
[docs-actions-url]: https://github.com/ethyca/fides/actions/workflows/publish_docs.yaml
[publish-actions-url]: https://github.com/ethyca/fides/actions/workflows/publish_package.yaml
[license-image]: https://img.shields.io/:license-Apache%202-blue.svg
[license-url]: https://www.apache.org/licenses/LICENSE-2.0.txt
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black/
[mypy-image]: http://www.mypy-lang.org/static/mypy_badge.svg
[mypy-url]: http://mypy-lang.org/
[twitter-image]: https://img.shields.io/twitter/follow/ethyca?style=social
[twitter-url]: https://twitter.com/ethyca
