# Meet Fides: Privacy as Code

[![Latest Release Version][release-image]][release-url]
[![Docker][docker-workflow-image]][docker-actions-url]
[![Docs][docs-workflow-image]][docs-actions-url]
[![Package][release-workflow-image]][publish-actions-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]
[![Twitter][twitter-image]][twitter-url]
[![Coverage](https://codecov.io/github/ethyca/fides/coverage.svg?branch=main)](https://codecov.io/gh/ethyca/fides)

![Fides banner](docs/fides/docs/img/fides-banner.png "Fides banner")

## :zap: Overview

Fides (pronounced */fee-dhez/*, from Latin: Fidēs) is an open-source privacy engineering platform for managing the fulfillment of data privacy requests in your runtime environment, and the enforcement of privacy regulations in your code.

## :rocket: Quick Start

### Getting Started

In order to get started quickly with Fides, a sample project is bundled within the Fides CLI that will set up a server, privacy center, and a sample application for you to experiment with.

#### Minimum requirements (for all platforms)

* [Docker](https://www.docker.com/products/docker-desktop) (version 20.10.11 or later)
* [Python](https://www.python.org/downloads/) (version 3.8 through 3.10)

#### Download and install Fides

> [!TIP]
> We highly recommend setting up a Python virtual environment such as `venv` to install Fides into. For example:
> 
> ```sh
> mkdir ~/fides
> cd ~/fides
> python3 -m venv venv
> source venv/bin/activate
> ```

Once your virtual environment is ready, you can easily download and install Fides using `pip`. Run the following command to get started:

```
pip install ethyca-fides
```

#### Deploy the Fides sample project

By default, Fides ships with a small project belonging to a fictional e-commerce store. Running the `fides deploy up` command builds a Fides project with all you need to run your first Data Subject Request against real databases.

```sh
fides deploy up
```

#### Explore the sample project

When your deployment finishes, a welcome screen will explain the key components of Fides and the sample "Cookie House" project.

If your browser does not open automatically, you should navigate to <http://localhost:3000/landing>.

The project contains:

* The Fides Admin UI for managing privacy requests
* The Fides [Privacy Center](https://docs.ethyca.com/fides/dsr_quickstart/privacy_center) for submitting requests
* The sample "Cookie House" eCommerce site for testing
* A DSR Directory on your computer to view results (`./fides_uploads`)

#### Run your first Privacy Access Request

Navigate to the Fides Privacy Center (<http://localhost:3001>), submit a "Download your data" request, provide the email address for the sample user (`jane@example.com`), and submit the request.

Then, navigate to the Fides Admin UI (<http://localhost:8080>) to review the pending privacy request.

Use username `root_user` and password `Testpassword1!` to login, approve the request, and review the resulting package in your `./fides_uploads` folder!

### Next Steps

Congratulations! You've just run an entire privacy request in under 5 minutes! Fides offers many more tools to help take control of your data privacy. To find out more, you can run a privacy request on [your own infrastructure](https://docs.ethyca.com/fides/dsr_quickstart/overview), discover [data mapping](https://docs.ethyca.com/fides/data_mapping/overview), or learn about the [Fides Taxonomy](https://ethyca.github.io/fideslang/).

## :book: Learn More

The Fides core team is committed to providing a variety of documentation to help get you started using Fides.  As such, all interactions are governed by the [Fides Code of Conduct](https://docs.ethyca.com/fides/community/code_of_conduct).

### Documentation

For more information on getting started with Fides, how to configure and set up Fides, and more about the Fides ecosystem of open source projects:

* Documentation: <https://docs.ethyca.com>
* Website: www.ethyca.com/fides

### Support

Join the conversation on:

* [Slack](https://fid.es/join-slack)
* [Twitter](https://twitter.com/ethyca)
* [Discussions](https://github.com/ethyca/fides/discussions)

### Contributing

We welcome and encourage all types of contributions and improvements!  Please see our [contribution guide](https://docs.ethyca.com/fides/community/overview) to opening issues for bugs, new features, and security or experience enhancements.

Read about the [Fides community](https://docs.ethyca.com/fides/community/hints_tips) or dive into the [contributor guides](https://docs.ethyca.com/fides/community/development/overview) for information about contributions, documentation, code style, testing and more. Ethyca is committed to fostering a safe and collaborative environment, such that all interactions are governed by the [Fides Code of Conduct](https://docs.ethyca.com/fides/community/code_of_conduct).

## :balance_scale: License

The [Fides](https://github.com/ethyca/fides) ecosystem of tools are licensed under the [Apache Software License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
Fides tools are built on [fideslang](https://github.com/ethyca/privacy-taxonomy), the Fides language specification, which is licensed under [CC by 4](https://github.com/ethyca/privacy-taxonomy/blob/main/LICENSE).

Fides is created and sponsored by Ethyca: a developer tools company building the trust infrastructure of the internet. If you have questions or need assistance getting started, let us know at fides@ethyca.com!

[release-image]: https://img.shields.io/github/release/ethyca/fides.svg
[release-url]: https://github.com/ethyca/fides/releases
[docker-workflow-image]: https://github.com/ethyca/fides/workflows/Docker%20Build%20&%20Push/badge.svg
[docs-workflow-image]: https://github.com/ethyca/fides/workflows/Publish%20Docs/badge.svg
[release-workflow-image]: https://github.com/ethyca/fides/actions/workflows/publish_package.yaml/badge.svg
[docker-actions-url]: https://github.com/ethyca/fides/actions/workflows/publish_docker.yaml
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

## ⚠️ Advanced Setup for Microsoft SQL Server (MSSQL) Support

By default, running `pip install ethyca-fides` locally will not install the optional Python libraries needed for Microsoft SQL Server, since these rely on additional system dependencies (`freetds`)! However, if you *do* want to connect to MSSQL, you have two options:
1. Use our pre-built Docker images which install these optional dependencies automatically: [`ethyca/fides`](https://hub.docker.com/r/ethyca/fides). See our [Deployment Guide](https://ethyca.com/docs/dev-docs/configuration/deployment) for more!
2. Install the required dependencies on your local development machine and run `pip install ethyca-fides[all]` to include "all" the optional libraries. Keep reading to learn more about this!

For local development setup on macOS, follow these steps:
1. Install the required development libraries from Homebrew:
```bash
brew install freetds openssl
```
2. Add the following to your shell (i.e. `.zshrc`) to ensure your compiler can access the `freetds` and `openssl` libraries, updating the paths & versions to match your local install:
```bash
export LDFLAGS="-L/opt/homebrew/Cellar/freetds/1.3.18/lib -L/opt/homebrew/Cellar/openssl@1.1/1.1.1u/lib"
export CFLAGS="-I/opt/homebrew/Cellar/freetds/1.3.18/include"
```
3. Reinstall Fides with MSSQL support by including the `all` extra requirement:
```bash
pip install ethyca-fides[all]
```
