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
No config file found. Using default configuration values.
Initializing Fidesctl...

Created a '.fides' directory.

Fides needs your permission to send Ethyca a limited set of anonymous usage statistics.
Ethyca will only use this anonymous usage data to improve the product experience, and will never collect sensitive or personal data.

***
Don't believe us? Check out the open-source code here:
    https://github.com/ethyca/fideslog
***

To opt-out of all telemetry, press "n". To continue with telemetry, press any other key.

Created a config file at '.fides/fidesctl.toml'. To learn more, see:  
            https://ethyca.github.io/fides/installation/configuration/

Fidesctl initialization complete.
```

## Configuring Fidesctl

See our [Configuration](../installation/configuration.md) guide for more information on how to configure fidesctl.

## Running the webserver

Now that we've spun up our database and set our configuration values, it's time to start our webserver. In a shell, run the following command:

```sh
fidesctl webserver
```

The fidesctl webserver will now be accessible at `localhost:8080`, you can test this by going to `localhost:8080/health` and `localhost:8080/docs`.

## Using the CLI

Now that the database and webserver are running, you can verify that the database is reachable from the webserver.

Run the command `fidesctl ls organizations` to verify that all is working. The output should look something like this:

```json
[
  {
    "fides_key": "default_organization",
    "organization_fides_key": "default_organization",
    "name": null,
    "description": null,
    "organization_parent_key": null
  }
]
```

That's it! Your local installation of fidesctl is completely up and running.

## Next Steps

See the [Tutorial](../tutorial/index.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
