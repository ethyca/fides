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

## Initializing Fidesctl

With fidesctl installed, it's time to initialize the project so we have some place to start adding resource manifests and tweaking our configuration. Run the following command and follow the prompts to get your local fidesctl instance initialized.

```sh title="Initialize Fidesctl"
fidesctl init
```

## Configuring Fidesctl

See our [Configuration](../installation/configuration.md) guide for more information on how to configure fidesctl.

## Run Fidesctl via Docker

Now that the dependency is included in the project and the configuration is in place, the fidesctl server needs to be told to run. The app uses `docker-compose` to orchestrate resources, so include `fidesctl` as a service by adding the following configuration after the database service:

```yaml
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
    - FIDESCTL__API__DATABASE_URL=postgres:postgres@db:5432/fidesctl
```

> See [the fidesctl installation guide](../installation/installation.md) for a more detailed fidesctl server setup walkthrough, and [the `docker-compose` documentation](https://docs.docker.com/compose/compose-file/) for an explanation of the above configuration options.

## Add `Makefile` Commands

> This step is optional, but the commands added to the `Makefile` here will be referenced later in this tutorial.

The above changes will enable fidesctl CLI commands to be run within the project's virtual environment. You can simplify usage of the fidesctl CLI by adding commands to the `Makefile` like the following:

```makefile
fidesctl-init-db: compose-up
	@echo "Initializing fidesctl db.."
	./venv/bin/fidesctl db init

fidesctl-evaluate: compose-up
	@echo "Evaluating policy with fidesctl..."
	./venv/bin/fidesctl evaluate --dry fides_resources

fidesctl-generate-dataset: compose-up
	@echo "Generating dataset with fidesctl..."
	./venv/bin/fidesctl generate dataset db postgresql://postgres:postgres@localhost:5432/flaskr example.yml
```

> **Note:** There are additional `Makefile` changes included in the `fidesdemo` repository, but they are only intended to enable cleaner usage of this project for demonstration purposes.

## Check Your Progress

After making the above changes, your app should resemble the state of the [`ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) at the [`fidesops-start`](https://github.com/ethyca/fidesdemo/releases/tag/fidesops-start) tag.

## Next: Annotate the Resources

Now that the fidesctl tools are available to use within the app's virtual environment, the next step is to configure fidesctl to work with the specifics of this app. This can be done by creating manifest files to [annotate the resources](dataset.md).
