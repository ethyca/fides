# Fides

[![Latest Version][pypi-image]][pypi-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]

## Overview

Fides (Latin: Fidēs) enables engineers and data teams to declaratively enforce data privacy requirements within the Software Development Life-Cycle.

With Fides, anyone working with risky types of data (e.g. personally identifiable information), can declare or describe their data intentions and Fides will continually evaluate compliance and warn users of unsafe changes _before_ they make it into production.

This approach ensures that privacy is described within your source code, thereby making privacy easier to manage and a proactive part of your existing software development practices.

## Principles

* Data Lineage Declarations
* Privacy controls at the CI layer
* Predefined Privacy Taxonomy
* Translation layer between engineers and lawyers

## Quick Guide

To make things more concrete, the following is a brief overview of the steps required to set up a new project with Fides as used by a monorepo:

1. Create a new directory for your Fides objects to live in, for examples `fides_manifests/`.

1. The next step is to define Fides objects as manifest files. This would include defining datasets, extending the privacy classifiers, and anything else needed to describe the state of the project's privacy.

1. Apply the manifests using `fidesctl apply fides_manifests/`. This command will create/update objects via the Fides API.

1. Set up a CI pipeline to run when the system file is changed. It should use the `fidesctl dry-evaluate <system_manifest> <system_key>` command to check that a system is still valid after it has been update.

1. Upon merge to the main branch, a pipeline should run to re-apply the `fides_manifests/` folder.

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
