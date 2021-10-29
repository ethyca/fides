# Meet Fidesops

_A part of the [greater Fides ecosystem](https://github.com/ethyca/fides)._

[![Latest Version][pypi-image]][pypi-url]
[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]
[![Fides Discord Server][discord-image]][discord-url]

## :zap: Overview

Fidesops (*fee-dez-äps*, combination of the Latin term "Fidēs" + "operations") is an extensible, deployed engine that fulfills any Data Subject Access Request (DSAR) and Right to be Forgotten (RTBF) request by connecting directly to your databases.

- **Programmable Data Privacy.** Fidesops connects and orchestrates calls to all of your databases in order to access, update and delete sensitive data per your policy configuration (TODO this needs a new name) written in [Fideslang](https://github.com/ethyca/fides).

- **DAGs for Datastores.** Fidesops works by integrating all your data store connections into a unified graph - also known as a DAG. We know that sensitive data is stored all around your dynamic ecosystem, so fidesops builds the DAG at runtime.

- **B.Y.O. DSAR Automation Provider.** Fidesops handles the integration to privacy management tools like OneTrust and Transcend to fulfill Data Subject Requests and returns the package back to the DSAR Automation provider.

- **Built to scale.** Lots of databases? Tons of microservices? Large distributed infrastructure? Connect as many databases and services as you'd like, and let fidesops do the heavy lifting (like auth management, failure retry, and error handling).

## :rocket: Quick Start - DSAR

If you're looking for a more detailed introduction to Fidesops, we recommend following [our tutorial here](https://github.com/ethyca/solon/blob/main/docs/fidesops/docs/index.md) (TODO UPDATE LINK WHEN TUTORIAL IS DONE). But to give Fidesops a test drive, follow these 5 easy steps:

1. First, follow the [Getting Started with Fidesops in Docker](https://github.com/ethyca/solon/docs/solon/docs/getting_started/docker.md) guide until your shell is ready.

2. Next, we'll create a policy configuration (TODO new name). You'll find an example below where we're instructing fidesops to access all user-provided email addresses, names, and phone numbers.

3. Now let's configure a storage location for your completed DSAR to upload to. Using the ARN for a publicly accessible AWS S3 bucket, you can ...

```bash
  PUT {host}/api/v1/storage/config
  {
    "destinations": [
      {
        "name": "s3 storage",
        "key": "{unique_key}",
        "type": "s3",
        "format": "json",
        "details": {
          "bucket": "{bucket_name}",
          "naming": "request_id"
        }
      }
    ]
  }

```

On success, the response will include a `storage_key`.

Use that `storage_key` in the following endpoint to authenticate with S3:

```bash
  PUT {host}/api/v1/storage/config/{storage_key}/secret
  {
    # s3
    "aws_access_key_id": "{aws_access_key_id}",
    "aws_secret_access_key": "{aws_secret_access_key}"
  }

```

1. Almost there! We'll hook up our quick-start database which is prepopulated with sample data (TODO)

2. Let's see it in action by creating your first Privacy Request. Navigate to `http://0.0.0.0:8080/docs#/Privacy%20Requests/create_privacy_request_api_v1_privacy_requests_post` and enter the following example...(TODO)

You've learned how to connect a database and storage location, create a policy config (TODO new name), and call the API to create a DSAR. But there's a lot more to discover, so we'd recommend following [the tutorial](https://github.com/solon/tutorial/) to keep learning.

## :book: Learn More

Fides provides a variety of docs to help guide you to a successful outcome.

We are committed to fostering a safe and collaborative environment, such that all interactions are governed by the [Fides Code of Conduct](https://github.com/ethyca/solon/blob/main/docs/solon/docs/community/code_of_conduct.md).

### Documentation

Full Fidesops documentation is available [here](https://github.com/ethyca/solon/blob/main/docs/solon/docs/).

### Support

Join the conversation on:

- [Discord](https://discord.gg/NfWXEmCsd4)
- [Twitter](https://twitter.com/ethyca)
- Discussions (TODO need to enable)

### Contributing

Read about the Fides [community](https://github.com/ethyca/solon/blob/main/docs/solon/docs/community/github.md) or dive in to the [development guides](https://github.com/ethyca/solon/blob/main/docs/solon/docs/development/overview.md) for information about contributions, documentation, code style, testing and more.

## :balance_scale: License

The Fides ecosystem of tools is licensed under the [Apache Software License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

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
