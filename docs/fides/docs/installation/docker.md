# Installation from Docker

For the ease of deployment in production, the community releases a production-ready reference container image.

The fidesctl community releases Docker Images which are reference images for fidesctl. Every time a new version of fidesctl is released, the images are available in the [ethyca/fidesctl DockerHub](https://hub.docker.com/r/ethyca/fidesctl/tags). There are also mid-release versions (dirty versions) that get uploaded to DockerHub on every commit to the main branch.

These reference images contain all of the extras and dependencies for running the Python application. However they do not contain the required Postgres database.

Fidesctl requires multiple components to function as it is a multi-part application. You may therefore also be interested in launching fidesctl in the Docker Compose environment, see: [Running Fidesctl in Docker](../quickstart/docker.md).
