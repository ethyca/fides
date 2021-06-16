# Fides

[![Latest Version][pypi-image]][pypi-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]

## Getting Started With Fides

1. Install Docker and Make
1. Clone the `https://gitlab.com/ethyca/fides-core` repo
1. Run `make init-db` in the top-level directory to prepare the database
1. `make cli` to start a shell within a `Fides CLI` container
1. Wait a minute or so for the server to be available, you can check this with `fidesctl connect`
1. `fidesctl` to get a list of possible commands

## Configuring Fides

### Application Variables

These are the environment variables that can be set to configure the CLI for a specific deployment:

* FIDES_SERVER_URL - The URL of the Fides webserver

### Manifests

Fides ships with default data taxonomies that include standard examples, but in practice you may need to create your own to match what your organization uses in practice. This is done in the same way as declaring other objects. The following is a list of steps to both define and validate new systems within Fides.

#### Creating objects

1. Create the necessary objects (reference the sample manifest files in the `fidesctl/data/samples/`)
1. `fidesctl apply <manifest_dir>/` to create the objects defined in that directory. This will create all objects _except_ for any systems contained within the manifest files.

## Rating your Systems

With your manifests defined, the next step is to “submit” your system for approval or rejection. This is done using the `fidesctl rate <path_to_system_manifests> <policy_id>` command. This will return an object that shows the status of the rating.

## Contributing

There are two components to the Fides project; the CLI and the Server. The CLI is a Python application and the Server is a Scala application powered by MySQL.

[pypi-image]: https://img.shields.io/pypi/v/fidesctl.svg
[pypi-url]: https://pypi.python.org/pypi/fidesctl/
[license-image]: https://img.shields.io/:license-Apache%202-blue.svg
[license-url]: https://www.apache.org/licenses/LICENSE-2.0.txt
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black 
