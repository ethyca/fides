# Meet Fidesops: Privacy as Code for DSAR Orchestration

_A part of the [greater Fides ecosystem](https://github.com/ethyca/fides)._

[![License][license-image]][license-url]
[![Code style: black][black-image]][black-url]
[![Checked with mypy][mypy-image]][mypy-url]
[![Twitter][twitter-image]][twitter-url]

![Fidesops banner](docs/fidesops/docs/img/fidesops.png "Fidesops banner")
## :zap: Overview

**Fidesops** (*fee-dez-äps*, combination of the Latin term "Fidēs" + "operations") is an extensible, [deployed](https://ethyca.github.io/fidesops/deployment/) engine that [fulfills any privacy request](https://ethyca.github.io/fidesops/guides/privacy_requests/) (e.g. access request, erasure request) by [connecting directly to your disparate databases](https://ethyca.github.io/fidesops/tutorial/postgres_connection/).

![Fidesops overview](docs/fidesops/docs/img/fidesops-overview-diagram.png "Fidesops overview")
## :rocket: Quick Start
If you're looking for a more detailed introduction to Fidesops, we recommend following [our tutorial here](https://ethyca.github.io/fidesops/tutorial/). 

Run the quickstart in your terminal to give Fidesops a test drive:

```
Install Docker: https://docs.docker.com/desktop/#download-and-install
Install Make: brew install make
```

```bash
git clone https://github.com/ethyca/fidesops.git
cd fidesops
make quickstart
```
This runs fidesops in docker along with the necessary data stores.  It also spins up a test postgres
database and a test mongo database to mimic your application.  This quickstart will walk you through executing privacy
requests against your system by making a series of API requests to fidesops.

Follow these five easy steps:

### Step One: Set up basic configuration (press `[enter]` to make each API request)

- Authenticate by creating an Access Token
- Connect to your application's postgres and mongo databases with ConnectionConfigs 
- Describe the types of data you have and their relationships with Datasets 
- Dictate where to upload your results with StorageConfigs (a local folder for now)

### Step Two: Define an Access Policy

Policies help describe what data you care about and how you want to manage it.  In this example, you'll create an `access` 
Policy,`example_request_policy`, to get all data with the data category: `user.provided.identifiable`.
  
### Step Three: Run a Privacy Request to Access Data

Finally, you can issue a Privacy Request using Policy `example_request_policy` across your test databases for `jane@example.com`.
The following response will be uploaded to a local folder (for demo purposes). We've collected identifiable user-provided
information for Jane across tables in both the postgres and mongo databases.

```json
{
  "mongo_test:flights": [
    {
      "passenger_information": {
        "full_name": "Jane Customer"
      }
    }
  ],
  "mongo_test:customer_details": [
    {
      "gender": "female",
      "children": [
        "Erica Example"
      ],
      "birthday": "1990-02-28T00:00:00"
    }
  ],
  "postgres_example:address": [
    {
      "city": "Example Mountain",
      "state": "TX",
      "house": 1111,
      "zip": "54321",
      "street": "Example Place"
    }
  ],
  "postgres_example:customer": [
    {
      "email": "jane@example.com",
      "name": "Jane Customer"
    }
  ],
  "mongo_test:rewards": [
    {
      "owner": [
        {
          "phone": "530-486-6983"
        },
        {
          "phone": "818-695-1881"
        }
      ]
    },
    {
      "owner": [
        {
          "phone": "254-344-9868"
        }
      ]
    }
  ],
  "mongo_test:employee": [
    {
      "email": "employee-2@example.com",
      "name": "Jane Employee"
    }
  ],
  "mongo_test:conversations": [
    {
      "thread": [
        {
          "ccn": "987654321",
          "chat_name": "Jane C"
        }
      ]
    },
    {
      "thread": [
        {
          "ccn": "987654321",
          "chat_name": "Jane C"
        },
        {
          "chat_name": "Jane C"
        }
      ]
    }
  ],
  "mongo_test:payment_card": [
    {
      "ccn": "987654321",
      "code": "123",
      "name": "Example Card 2"
    }
  ],
  "postgres_example:payment_card": [
    {
      "ccn": 373719391,
      "code": 222,
      "name": "Example Card 3"
    }
  ]
}

```

### Step Four: Create an Erasure Policy

Now you'll create another Policy, `example_erasure_policy`, that describes how to `erase` data with the same category, by replacing values with null.


### Step Five: Issue a Privacy Request to erase data and verify

The last step is to issue a Privacy Request using `example_erasure_policy` to remove identifiable user-provided data 
related to "jane@example.com". Then we'll re-run step #3 again to see what data is remaining for data category `user.provided.identifiable`:

```json
{}
```
This returns an empty dictionary confirming Jane's fields with data category `user.provided.identifiable` have been removed.


You've learned how to use the Fidesops API to connect a database and a final storage location, define policies that describe
how to handle user data, and execute access and erasure requests.  But there's a lot more to discover,
so we'd recommend following [the tutorial](https://ethyca.github.io/fidesops/tutorial/) to keep learning.

### Documentation

For more information on getting started with Fidesops, how to configure and set up Fidesops, and more about the Fides ecosystem of open source projects: 

- Documentation: https://ethyca.github.io/fidesops/
- How-to guides: https://ethyca.github.io/fidesops/guides/oauth/
- Deployment: https://ethyca.github.io/fidesops/deployment/
- Roadmap: https://github.com/ethyca/fidesops/milestones
- Website: www.ethyca.com/fides


### Support

Join the conversation on:

- [Slack](https://fid.es/join-slack)
- [Twitter](https://twitter.com/ethyca)
- [Discussions](https://github.com/ethyca/fidesops/discussions)

### Contributing

We welcome and encourage all types of contributions and improvements!  Please see our [contribution guide](CONTRIBUTING.md) to opening issues for bugs, new features, and security or experience enhancements.

Read about the [Fides community](https://ethyca.github.io/fidesops/community/github/) or dive into the [development guides](https://ethyca.github.io/fidesops/development/overview) for information about contributions, documentation, code style, testing and more. Ethyca is committed to fostering a safe and collaborative environment, such that all interactions are governed by the [Fides Code of Conduct](https://ethyca.github.io/fidesops/community/code_of_conduct/).

## :balance_scale: License

The Fides ecosystem of tools ([Fidesops](https://github.com/ethyca/fidesops) and [Fidesctl](https://github.com/ethyca/fides)) are licensed under the [Apache Software License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
Fides tools are built on [Fideslang](https://github.com/ethyca/privacy-taxonomy), the Fides language specification, which is licensed under [CC by 4](https://github.com/ethyca/privacy-taxonomy/blob/main/LICENSE). 

Fides is created and sponsored by [Ethyca](https://ethyca.com): a developer tools company building the trust infrastructure of the internet. If you have questions or need assistance getting started, let us know at fides@ethyca.com!


[license-image]: https://img.shields.io/:license-Apache%202-blue.svg
[license-url]: https://www.apache.org/licenses/LICENSE-2.0.txt
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black/
[mypy-image]: http://www.mypy-lang.org/static/mypy_badge.svg
[mypy-url]: http://mypy-lang.org/
[twitter-image]: https://img.shields.io/twitter/follow/ethyca?style=social
[twitter-url]: https://twitter.com/ethyca
