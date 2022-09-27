# Overview

The Fides team provides up-to-date versions of both PyPI and Docker installations. For information on which method of installation might work best for your use, the requirements for each option is summarized below.

## Installation options
### PyPI

Only `pip`/`pipx` installations are currently officially supported. For more information, see [Installation from PyPI](pypi.md).

!!! Tip "For environment isolation, the Fides team recommends using [`pipx`](https://pypa.github.io/pipx/) when possible."

#### When to use PyPI
* If you are not familiar with Docker or containers, and want to install Fides on physical or virtual machines. 
* If you are used to installing and running software using custom deployment mechanism.
* If you would like to use with a lightweight installation of Fides, and manage optional dependencies on your own.

#### Intended users
* Users who are familiar with installing and configuring Python applications, managing Python environments and dependencies, and running software with their custom deployment mechanisms.

#### Requirements
* You are expected to install Fides and any associated components on your own.
* You will develop and handle the deployment for all components of Fides.
* You are responsible for setting up the databases, configuring automated startup and recovery, and handling maintenance, cleanup, and upgrades.

#### Additional support 
* The [Installation from PyPI](pypi.md) guide provides installation details. Due to differences in environments and tools, this guide cannot comprehensively cover all deployment and usage errors and concerns.

### Docker

The Fides Docker images are built by the Fides CI/CD pipeline, which generates versions on each official release, as well as commits made to the main branch. For this reason, it is highly discouraged to use the `latest` tag, as any non-official release versions may contain some instability. For more information, see [Installation from Docker](docker.md).

#### When to use Docker
* If you are looking for the quickest way to get started, with minimal additional configuration. Docker will run Fides components in isolation from other software running on the same physical or virtual machines, and provides straightforward dependency maintenance.
* If you are familiar with the container/Docker stack. 

#### Intended users

* Users who are familiar with containers and Docker, and understand how to build and extend their own container images.
* Users who know how to create and maintain Docker deployments.

#### Requirements
* You may need to Customize or extend the container or Docker images to add extra dependencies. 
* You will build deployments out of several containers (i.e., via Docker Compose).
* You are responsible for setting up the databases, configuring automated startup and recovery, and handling maintenance, cleanup, and upgrades.
* You should choose the right deployment mechanism (a custom process, Kubernetes, Docker Compose, Helm charts, etc.) based on your experience and expectations.

### Troubleshooting
* For questions regarding either installation, visit the [Community](../community/overview.md) page.
