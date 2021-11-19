# Add Fidesctl to the App

In this step you will incorporate [fidesctl](https://github.com/ethyca/fides), which will enable you to declare your `system`, `dataset`, and `policy` resources as manifest YAML files.

## Add the `fidesctl` Dependency

Open the `requirements.txt` file and add the `fidesctl` dependency by including the following line:

```txt
fidesctl>=1.0.0
```

Then, install the dependencies by running:

```sh
pip install -r requirements.txt
```

## Configure Fidesctl

Fidesctl needs some configuration to work for your environment; this is handled by looking for a TOML file in the current working directory. Create a `fidesctl.toml` file at the root level of the repository. It should contain the following configuration:

```toml
[cli]
server_url = "http://localhost:8080"

[api]
database_url = "postgresql://postgres:postgres@localhost:5432/fidesctl"
```

- The `[cli]`-scoped `server_url` option specifies the address that the fidesctl CLI will use when connecting to the fidesctl server.
- The `[api]`-scoped `database_url` option specifies the connection string that the fidesctl API will use to connect to the PostgreSQL database created in the previous step.

## Run Fidesctl via Docker

Now that the dependency is included in the project and the configuration is in place, the fidesctl server needs to be told to run. The app uses `docker-compose` to orchestrate resources, so include `fidesctl` as a service by adding the following configuration after the database service:

```yml
fidesctl:
  image: ethyca/fidesctl:latest
  depends_on:
    - db
  command: fidesctl webserver
  expose:
    - 8080
  ports:
    - "8080:8080"
  environment:
    - FIDESCTL__API__DATABASE_URL=postgresql://postgres:postgres@db:5432/fidesctl
```

> See [the fidesctl deployment guide](../installation/installation.md) for a more detailed fidesctl server setup walkthrough, and [the `docker-compose` documentation](https://docs.docker.com/compose/compose-file/) for an explanation of the above configuration options.

## Add `Makefile` Commands

> This step is optional, but the commands added to the `Makefile` here will be referenced later in this tutorial.

The above changes will enable fidesctl CLI commands to be run within the project's virtual environment. You can simplify usage of the fidesctl CLI by adding commands to the `Makefile` like the following:

```makefile
fidesctl-init-db: compose-up
	@echo "Initializing fidesctl db.."
	./venv/bin/fidesctl init-db

fidesctl-evaluate: compose-up
	@echo "Evaluating policy with fidesctl..."
	./venv/bin/fidesctl evaluate --dry fides_resources

fidesctl-generate-dataset: compose-up
	@echo "Generating dataset with fidesctl..."
	./venv/bin/fidesctl generate-dataset postgresql://postgres:postgres@localhost:5432/flaskr example.yml
```

> **Note:** There are additional `Makefile` changes included in the `fidesdemo` repository, but they are only intended to enable cleaner usage of this project for demonstration purposes.

## Check Your Progress

After making the above changes, your app should resemble the state of the [`ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) at the [`fidesops-start`](https://github.com/ethyca/fidesdemo/releases/tag/fidesops-start) tag.

## Next: Annotate the Resources

Now that the fidesctl tools are available to use within the app's virtual environment, the next step is to configure fidesctl to work with the specifics of this app. This can be done by creating manifest files to [annotate the resources](dataset.md).
