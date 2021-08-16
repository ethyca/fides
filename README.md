# Fides

[![Latest Version][pypi-image]][pypi-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]

## Overview

Fides (*fee-dez*, Latin: Fidēs) is the modern framework for data teams to implement data privacy requirements using all your existing CI/CD tools.

- **A Privacy Grammar for Engineers.** Fides is a way for you to declare when, where and how you plan to use risky types of data (e.g. personally identifiable information) directly in your code. 

- **Privacy Policies That Aren't Just for Lawyers.** Fides allows you to make a privacy policy that's *actually* enforced at time of integration and deployment.

- **CI/CD/CP.** Update your policies and data systems as frequently as you (or your legal team!) needs. The updated policies will continuously evaluate compliance and warn users of unsafe changes _before_ they make it into production.

- **Built to Scale.** Lots of databases? Tons of microservices? Large distributed infrastructure? Fides defines the data privacy taxonomy that allows for both lawyers and engineers to work together with a common language, so that the policies and rules can be applied across the entire data ecosystem.


## Getting Started

Getting set up with Fides for a monorepo just 5 steps:

1. Create a new directory for your Fides objects to live in, for example, `fides_manifests/`.

1. Define and extend existing Fides objects as "manifest files". You can define datasets, extend the privacy classifiers, and anything else needed to describe the state of your business' privacy.

1. Apply the manifest files using `fidesctl apply fides_manifests/`. This command will create and update objects via the Fides API.

1. Set up a CI pipeline to run when the system file is changed. It should use the `fidesctl dry-evaluate <system_manifest> <system_key>` command to check that a system is still valid after it has been update.

1. On merge to the main branch, a pipeline should run to re-apply the `fides_manifests/` folder.

For more information on getting started, see the [tutorial docs]().

## Resources

### Documentation

Fides' documentation is available [here]().

### Contributing

Read about the Fides [community]() or dive in to the [development guides]() for information about contributions, documentation, code style, testing and more.

[pypi-image]: https://img.shields.io/pypi/v/fidesctl.svg
[pypi-url]: https://pypi.python.org/pypi/fidesctl/
[license-image]: https://img.shields.io/:license-Apache%202-blue.svg
[license-url]: https://www.apache.org/licenses/LICENSE-2.0.txt
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black/
[mypy-image]: http://www.mypy-lang.org/static/mypy_badge.svg
[mypy-url]: http://mypy-lang.org/
