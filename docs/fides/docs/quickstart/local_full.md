# Running Fidesctl Locally (Full Installation)

---

Fidesctl can be spun up locally in its entirety without relying on Docker, but it is a bit more complicated. If you'd like something simpler, please see the [Running Fidesctl in Docker](docker.md) guide for the recommended setup experience or [Running Fidesctl Locally (Standalone)](local_standalone.md) for the simplest possible installation.

## System Requirements

See the [Prerequisites and Dependencies](../installation/prerequisites_dependencies.md) page for more information.

## Fidesctl installation

The next step is to install fidesctl via pip with the required extras:

```sh
pip install "fidesctl[webserver]"
```

For more information on pip installing fidesctl as well as the other potential extras, see the [Installation from PyPI](../installation/pypi.md) guide.

## Database installation

Due to environmental differences, there is no specific guide on running/configuring your own Postgres database outside of the version constraints mentioned in the `System Requirements` section above.

Make sure to note your database credentials and use them to generate a [SQLAlchemy Connection String](https://docs.sqlalchemy.org/en/14/core/engines.html#postgresql). This will be used in the `database_url` configuration value mentioned below.

## Initializing Fidesctl

With Fidesctl installed, it's time to initialize the project so we have some place to start adding resource manifests and tweaking our configuration.

```sh title="Initialize Fidesctl"
fidesctl init
```

```txt title="Expected Output"
Initializing Fidesctl...
----------
Created a './.fides' directory.
----------
Created a fidesctl config file: ./.fides/fidesctl.toml
To learn more about configuring fidesctl, see:
    https://ethyca.github.io/fides/installation/configuration/
----------
For example policies and help getting started, see:
    https://ethyca.github.io/fides/guides/policies/
----------
Fidesctl initialization complete.
```

## Configuring Fidesctl

See our [Configuration](../installation/configuration.md) guide for more information on how to configure fidesctl.

## Running the webserver

Now that we've spun up our database and set our configuration values, it's time to start our webserver. In a shell, run the following command:

```sh
fidesctl webserver
```

The fidesctl webserver will now be accessible at `localhost:8080`, you can test this by going to `localhost:8080/api/v1/health` and `localhost:8080/docs`.

## Using the CLI

Now that the database and webserver are running, it's time to verify that the whole installation is working properly. Run the command `fidesctl status` to make sure that the CLI can talk to the webserver. The output should look something like this:

```txt
root@2da501a72f8f:/fides/fidesctl# fidesctl status
Getting server status...
Server is reachable and the client/server application versions match.
```

That's it! Your local installation of fidesctl is completely up and running.

## Next Steps

See the [Tutorial](../tutorial/index.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
