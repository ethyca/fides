# Getting Started with Fidesctl Manually (without Docker)

---

Fidesctl can be spun up locally without relying on Docker, but it is a bit more complicated. If you'd like something simpler, please see the [Running Fidesctl in Docker](docker.md) guide for the recommended setup experience.

## System Requirements

See the [Prerequisites and Dependencies](../installation/prerequisites_dependencies.md) page for more information.

## Fidesctl installation

The next step is to install fidesctl via pip with the required extras:

```sh
pip install "fidesctl[webserver]"
```

For more information on pip installing fidesctl as well as the other potential extras, see the [Installation from PyPI](../installation/pypi.md) guide.

## Database installation

Due to environmental differences, there is no specific guide on running/configuring your own postgres database outside of the version constraints mentioned in the `System Requirements` section above.

Make sure to note your database credentials and use them to generate a [SQLAlchemy Connection String](https://docs.sqlalchemy.org/en/14/core/engines.html#postgresql). This will be used in the `database_url` configuration value mentioned below.

## Configuring Fidesctl

See our [Configuration](../installation/configuration.md) guide for more information on how to configure fidesctl.

## Running the webserver

Now that we've spun up our database and set our configuration values, it's time to start our webserver. In a shell, run the following command:

```sh
fidesctl webserver
```

The fidesctl webserver will now be accessible at `localhost:8080`, you can test this by going to `localhost:8080/health` and `localhost:8080/docs`.

## Using the CLI

Now that the database and webserver are running, it's time to verify that the whole installation is working properly. Run the command `fidesctl ping` to make sure that the CLI can talk to the webserver. The output should look something like this:

```txt
Pinging http://fidesctl:8080/health...
{
    "data": {
        "message": "Fidesctl API service is healthy!"
    }
}
```

Next is to verify that the database is reachable from the webserver. Run the command `fidesctl ls organizations` to verify that all is working. The output should look something like this:

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
