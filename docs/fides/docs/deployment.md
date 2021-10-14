# Deployment Guide

Most of the examples in this documentation focus on a simple setup where everything runs *locally* on your development machine. But to actually leverage the benefits of Fidesctl with a team, you'll need to deploy this to a hosted environment where your developer team can collaborate.

A fully deployed Fidesctl environment can be broken down into four parts:

1. **Hosted Database**: Postgres database server used by the web server to persist state.
1. **Hosted Web Server**: Shared instance of `fidesctl webserver` that acts as a "source-of-truth" for shared resources, is accessible to all developers and CI.
1. **Developer Machines**: Developers running `fidesctl` locally when updating resource files.
1. **CI Build Server**: Run automated `fidesctl evaluate` commands both pre- and post-merge, to enforce policy as part of continuous integration.

![Deployment Diagram](img/Deployment_Diagram.svg)

We'll explain how to setup each of these parts individually, starting with the database.

## Step 1: Setup Hosted Database

Fidesctl's database requirements are quite modest; any hosted Postgres DB will do, as long as it's accessible by the webserver. Good options include:

* Managed Postgres database services (e.g. AWS RDS, GCP Cloud SQL, Azure Database)
* Self-hosted Postgres Docker container with a persistent volume mount (e.g. on a Kubernetes cluster)
* Self-hosted Postgres server (e.g. on an EC2 server)

NOTE: there *is no reason to expose this database to the public Internet* as long as it is will be accessible by your Fidesctl webserver!

Setting up a production-grade Postgres database is likely something your team is already familiar with, so we won't revisit that here. Once it's up and running, all you'll need is the **connection string** that includes the host, user, password, database, etc. Specifically, you'll need a SQLAlchemy-compatible connection string using psycopg2 ([docs here](https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#dialect-postgresql-psycopg2-connect)), like:

```txt
postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]
```

For example:

```txt
postgresql+psycopg2://fidesuser:fidespassword@my-database-server.example.com:5432/fidesctl
```

Keep these database connection credentials around as we'll need them in the next step.

## Step 2: Setting up the Fidesctl Web Server

The `fidesctl` tool can be used for both CLI commands *and* to run the web server. Internally, the web server is a [FastAPI](https://fastapi.tiangolo.com/) application with a [Uvicorn](https://www.uvicorn.org/) server to handle requests. To start a server instance, run `fidesctl webserver` and it will start serving up on port 8080.

The web server requires a single configuration variable, `database_url` to function. To provide this you'll need to create a minimal config toml file like the following, replacing the connection string with the one you created in step 1:

```toml
[api]
database_url = "postgresql+psycopg2://user:password@host:port/dbname"
```

Save this file as `fidesctl.toml` on the host you're using for the web server. Now, you'll need to get `fidesctl` installed in one of two ways: *docker pull* or *pip install*.

### Option 1: Installing fidesctl from Docker Hub

If you typically run your applications via Docker, you'll probably be familiar with pulling images and configuring them with environment variables. Setting up a `fidesctl webserver` should contain no surprises.

You can `docker pull ethyca/fidesctl` to get the latest image from Ethyca's Docker Hub here: [ethyca/fidesctl](https://hub.docker.com/r/ethyca/fidesctl).

```bash
~% docker pull ethyca/fidesctl
```

Once pulled, you can run `docker run ethyca/fidesctl fidesctl webserver` to start the server, and provide a few arguments:

* `-p 8080:8080`: binds port 8080 (the webserver) to port 8080 on the host, so you can connect from the outside
* `--env FIDESCTL__API__DATABASE_URL=<database_url>`: overrides the default database URL to the one you created in step 1

Putting this together:

```bash
~% docker run \
  -p 8080:8080 \
  --env FIDESCTL__API__DATABASE_URL="postgresql+psycopg2://user:password@host:port/dbname" \
  ethyca/fidesctl \
  fidesctl webserver
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

Now, for most Docker hosts, you won't be calling `docker run` directly, and instead will be providing configuration variables to Kubernetes/Swarm/ECS/etc. As you can see in the `docker run` example above, this config is quite minimal and should just involve specifying (1) the image, (2) the port mapping, (3) the `FIDESCTL__API__DATABASE_URL` environment variable.

Note that there's no need for a persistent volume mount for the web server, it's fully ephemeral and relies on the database for all it's permanent state.

### Option 2: Installing fidesctl from PyPI

Releases of `fidesctl` are published to PyPI here: [fidesctl](https://pypi.org/project/fidesctl/). Typically you'll setup a virtual environment and then run `pip install`:

```bash
(venv) ~% pip install fidesctl
```

Once installed, you can run `fidesctl -f fidesctl.toml webserver` to start the server using the `fidesctl.toml` file we created earlier:

```bash
(venv) ~% fidesctl -f fidesctl.toml webserver
INFO:     Started server process [19878]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

Ensure that you set up your web server to run this command on startup and map port 8080 as necessary.

### Testing the Web Server

Once the server is running, confirm you know the it's URL, as you'll need this configuration variable (`server_url`) in the next step.

To test that it's running, visit `http://{server_url}/health` in your browser and you should see `{{"data":{"message":"Fides service is healthy!"}}}`

## Step 3: Installing Fidesctl CLI on your Developer Machines

Next, we'll get Fidesctl installed as a dependency and configure it to connect to the server from Step 2. As before, you can do this either via PyPI or Docker Hub, though in this case it'll depend heavily on the language used for your project itself: Python projects will naturally find it easy to `pip install` another dependency, whereas Javascript/Ruby/Java/Go projects will likely find Docker more convenient (NOTE: we'd love to distribute builds for other package managers to simplify this - PRs welcome!).

### Option 1: Python Projects (via pip install)

For this example, we'll assume you've already got a git repo for your project (e.g. `/git/my-test-fides-project`) that has a `dev-requirements.txt` file to manage development dependencies. Add `fidesctl` to your requirements file (selecting a release version as desired) and run `pip install`:

```bash
(venv) ~/git/my-test-fides-project% cat dev-requirements.txt
fidesctl
(venv) ~/git/my-test-fides-project% pip install -r dev-requirements.txt
...
Installing collected packages: fidesctl
Successfully installed fidesctl-<VERSION>
```

Now create a minimal `fidesctl.toml` file with the following contents, replacing the server URL value with the details from step 2:

```toml
[cli]
server_url = "http://host:port"
```

Test out this new config file with a `fidesctl ping` command to ensure you can reach the server. Fidesctl will automatically look in the current directory for a file named `fidesctl.toml`, or you can specify it with the `-f` flag. For example, if you've installed locally:

```bash
(venv) ~/git/my-test-fides-project% fidesctl -f fidesctl.toml ping
Pinging http://host:port...
Ping Successful!
```

If this doesn't work, go back to step 2 and troubleshoot your server setup and ensure it's accessible from developer machines.

Lastly, ensure you check-in the changes to `dev-requirements.txt` and the new `fidesctl.toml` file to your git repo:

```bash
(venv) ~/git/my-test-fides-project% git add dev-requirements.txt
(venv) ~/git/my-test-fides-project% git add fidesctl.toml
(venv) ~/git/my-test-fides-project% git commit -m "Add fidesctl to repo"
[master (root-commit) e811212] Add fidesctl to repo
```

You can now use any `fidesctl` commands as part of your developer environment!

### Option 2: Non-Python Projects

For non-Python projects, you've got two options:

1. Install `fidesctl` globally using `pip install` without using a project-specific Python virtual env
2. Use `docker run ethyca/fidesctl` commands instead

Note that, just like when using `docker run` for the web server, you can specify the `FIDESCTL__CLI__SERVER_URL` environment variable to the container instead of a config file if you prefer:

```bash
~% docker run --env FIDESCTL__CLI__SERVER_URL=http://host:port ethyca/fidesctl fidesctl ping
```

Both of these options are a bit messier than with Python projects, but hopefully you can see how you'd update your development environment setup instructions to include one of these two options. The global `pip install` option works largely the same as in a Python project, except you'll also likely need to instruct developers to install Python 3+ and run the `pip install fidesctl` command manually. The `docker run` option works too, it's just less intuitive, so you may want to consider wrapping your typical commands (`ping`, `evaluate --dry`, etc.) with some scripts for convenience (e.g. `make` targets, `npm scripts`). This is largely a matter of preference, so we'll leave this up to you to figure out how to best integrate this into your development workflow.

## Step 4: Initialize the Web Server Database

Next, we'll initialize the database to use for the web server. Now that you've got the `fidesctl` CLI connected from your developer machine, this is as simple as running one command:

```bash
(venv) ~/git/my-test-fides-project% fidesctl init-db
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
----------
Processing organization resources...
CREATED 1 organization resources.
UPDATED 0 organization resources.
SKIPPED 0 organization resources.
----------
Processing data_category resources...
CREATED 77 data_category resources.
UPDATED 0 data_category resources.
SKIPPED 0 data_category resources.
----------
Processing data_use resources...
CREATED 23 data_use resources.
UPDATED 0 data_use resources.
SKIPPED 0 data_use resources.
----------
Processing data_subject resources...
CREATED 15 data_subject resources.
UPDATED 0 data_subject resources.
SKIPPED 0 data_subject resources.
----------
Processing data_qualifier resources...
CREATED 5 data_qualifier resources.
UPDATED 0 data_qualifier resources.
SKIPPED 0 data_qualifier resources.
----------
```

If you get a database connection error here, it means you've misconfigured the database URL in step 2, so go back and troubleshoot from there.

Once the database is initialized, you're ready to use the `fidesctl` CLI in your project. The final step is to setup your CI build server to automatically run the core `fidesctl` commands as part of your CI workflow.

## Step 5: Installing Fidesctl CLI on CI Build Server

Nowadays, most CI providers tend to have simple solutions to run Docker images, so you can follow the setup instructions from step 2 to `docker pull ethyca/fidesctl` in your CI scripts (also see step 2 for how to set `FIDESCTL__CLI__SERVER_URL` accordingly to point to your hosted web server). You'll want to use commands like `fidesctl ping` in some test CI actions at first, to make sure that your web server is connected, and then you can move on to automating your CI workflow.

See the [Integrate your CI](tutorial/ci.md) tutorial for more detail on what kinds of CI actions make sense, but generally you'll want to configure two:

1. Run `fidesctl evaluate --dry <path/to/resources>` as a "check" on every commit for development branches (or at least for every pull request)
2. Run `fidesctl evaluate <path/to/resources>` on every commit to your main branch

If you've configured everything correctly up until now, both your developer machines and your CI build server should be able to access the same shared `fidesctl webserver` instance from step 2, meaning you've got a hosted, persistent, shared environment for privacy metadata at your organization. Congrats!
