# Installation

This page describes installation options that you might use when considering how to install fidesctl. Fidesctl consists of multiple components, possibly distributed among various physical or virtual machines. Fidesctl can be deployed flexibly, meeting the needs of various environments with different levels of complexity.

You should also check-out the [prerequisites](prerequisites_dependencies.md) that must be fulfilled when installing fidesctl. Fidesctl requires additional [dependencies](prerequisites_dependencies.md) to be installed - which can be done via `extras`.

When you install fidesctl, you need to [setup the database](database.md) which must also be kept updated when fidesctl is upgraded.

## Installation Tools

Only `pip` installations are currently officially supported. For more details see [Installation from PyPI](pypi.md)

In some cases a lightweight installation might be desired, for instance, if the webserver is not needed. If this is the case, our `pip` installation supports optional dependencies.

While there are some successes with using other tools like poetry or pip-tools, they do not share the same workflow as the supported tools - especially when it comes to constraint vs. requirements management. Installing via Poetry or pip-tools is not currently supported. If you wish to install fidesctl using those tools you do so at your own discretion.

**When this option works best**

* This installation method is useful when you are not familiar with containers and Docker and want to install fidesctl on physical or virtual machines and you are used to installing and running software using custom deployment mechanism.
* The only officially supported mechanisms of installation is pip.

**Intended users**

* Users who are familiar with installing and configuring Python applications, managing Python environments, dependencies and running software with their custom deployment mechanisms.

**What are you expected to handle**

* You are expected to install fidesctl - all components of it - on your own.
* You should develop and handle the deployment for all components of fidesctl.
* You are responsible for setting up the database, automated startup and recovery, maintenance, cleanup and upgrades of fidesctl.

**What the Fidesctl community provides for this method**

* You have [Installation from PyPI](pypi.md) on how to install the software but due to various environments and tools you might want to use, you might expect that there will be problems which are specific to your deployment and environment that you will have to diagnose and solve.
* You have the [Running fidesctl Locally](../quickstart/local_full.md) guide where you can see an example of running fidesctl with minimal dependencies and setup. You can use this guide to start fidesctl quickly for local testing and development, however this is only intended to provide inspiration, not to represent a production-grade installation.

**Where to ask for help**

* For quick and general troubleshooting questions, visit the #troubleshooting channel on the fidesctl Slack. For longer discussions or to share information, visit the [GitHub discussions](https://github.com/ethyca/fides/discussions) page.
* If you can provide description of a reproducible problem with the fidesctl software, you can open issue in [GitHub issues](https://github.com/ethyca/fides/issues).

## Using Production Docker Images

More details: [Installation from Docker](docker.md)

**When this option works best**

* This installation method is useful if you are familiar with the container/Docker stack. It provides a capability of running fidesctl components in isolation from other software running on the same physical or virtual machines with easy maintenance of dependencies.
* The images are built by fidesctl CI/CD pipelines and offer versions for official releases as well as for every commit made to the main branch. For this reason, it is highly discouraged to use the `latest` tag, as any non-official release versions may contain some instability.

**Intended users**

* Users who are familiar with containers and Docker stack and understand how to build and extend their own container images.
* Users who know how to create deployments using Docker by linking together multiple Docker containers and maintaining such deployments.

**What are you expected to handle**

* You are expected to be able to customize or extend container/Docker images if you want to add extra dependencies. You are expected to put together a deployment built of several containers (for example using docker-compose) and to make sure that they are linked together.
* You are responsible for setting up the database, automated startup and recovery, maintenance, cleanup and upgrades of fidesctl.
* You should choose the right deployment mechanism. There a number of available options of deployments of containers. You can use your own custom mechanism, custom Kubernetes deployments, custom Docker Compose, custom Helm charts etc., and you should choose it based on your experience and expectations.

**What the Fidesctl community provides for this method**

* You have [Running Fidesctl in Docker](../quickstart/docker.md) where you can see an example of how to start fidesctl quickly for local testing and development. However this is just an inspiration. Do not expect to use this docker-compose.yml file for production installation, you need to get familiar with Docker Compose and its capabilities and build your own production-ready deployment with it if you choose Docker Compose for your deployment.
* The Docker Image is managed by the same people who build fidesctl, and they are committed to keeping it updated whenever new features and capabilities of fidesctl are released.

**Where to ask for help**

* For quick and general troubleshooting questions, visit the #troubleshooting channel on the fidesctl Slack. For longer discussions or to share information, visit the [GitHub discussions](https://github.com/ethyca/fides/discussions) page.
* If you can provide description of a reproducible problem with the fidesctl software, you can open issue in [GitHub issues](https://github.com/ethyca/fides/issues).
