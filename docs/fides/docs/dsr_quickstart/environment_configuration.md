Once your compute instance is set up, you can install Fides. Fides is available via maintained packages on [PyPI](https://pypi.org/project/fides/) and through Ethyca's [DockerHub](https://hub.docker.com/r/ethyca/fides).

## Running Fides via Docker
The Fides docker image is published on the [ethyca/fides DockerHub](https://hub.docker.com/r/ethyca/fides/tags) and maintained by the Fides team. 

### Installation
Run the following command to pull the latest image from Ethyca's [DockerHub](https://hub.docker.com/r/ethyca/fides):

```
docker pull ethyca/fides
```

To pull the Fides [Privacy Center](./privacy_center.md), run the following:
```
docker pull ethyca/fides-privacy-center
```

### Running the webserver
Once downloaded, you can start the Fides UI and database:
```
docker compose up -d
```

To open an interactive shell and connect to the CLI, run the following:
```
docker compose exec -it fides-poc /bin/bash
```

With the Fides webserver running, the hosted UI is available at `http://{server_url}/` (e.g. `http://localhost:8080/`). 

---

## Installing Fides via Pip
The Fides Python package is [published on PyPI](https://pypi.org/project/fides/) and maintained by the Fides team.
### Installation 
To install Fides, run:

```sh
pipx install fides
```
#### Initialize Fides

Initializing the project will create a configuration file with default values, and generate a directory to house your Fides resources.

```sh title="Initialize Fides"
fides init
```

```txt title="Expected Output"
Initializing Fides...
----------
Created a './.fides' directory.
----------
Created a fides config file: ./.fides/fides.toml
To learn more about configuring fides, see:
    https://ethyca.github.io/fides/installation/configuration/
----------
For example policies and help getting started, see:
    https://ethyca.github.io/fides/guides/policies/
----------
Fides initialization complete.
```

#### Running the webserver

In a shell, run the following command:

```sh
fides webserver
```

With the Fides webserver running, the hosted UI is available at `http://{server_url}/` (e.g. `http://localhost:8080/`). 

## Additional resources
For more information on customizing your environment configuration, see the [configuration reference](../installation/configuration.md) guide.

## Next steps
Now that your webserver is running, you are ready to [add Connectors](./configure_connectors.md).