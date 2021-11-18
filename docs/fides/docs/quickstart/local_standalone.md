# Running Fidesctl Locally (Standalone)

This method of running fidesctl requires zero dependencies outside of Python and a default pip installation of fidesctl. It is intended as the fastest possible quick start and is not designed for production-grade deployments.

In standalone mode most CLI commands will not work as they require webserver connectivity for persistence, and so those commands are not available. Crucially though, the core evaluation functionality is still present. To run in standalone mode, use one of the following methods:

```sh title="CLI flag"
fidesctl --local <subcommand>
```

```toml title="fidesctl.toml"
[cli]
local_mode = true
```

For more information on running a full fidesctl installation, see the [Running Fidesctl Locally (Full Installation)](local_full.md) or [Running Fidesctl in Docker](docker.md) pages.

## System Requirements

See the Python section of the [Prerequisites and Dependencies](../installation/prerequisites_dependencies.md) page for more information.

## Fidesctl Installation

The next step is to install fidesctl via pip:

```sh
pip install fidesctl
```

For more information on pip installing fidesctl as well as the other potential extras, see the [Installation from PyPI](../installation/pypi.md) guide.

## Using the CLI

Now that we have fidesctl installed, let's verify the installation:

```sh title="Command"
fidesctl --version
```

```txt title="Expected Output"
fidesctl, version 1.0.0
```

That's it! Your local standalone installation of fidesctl is up and running.

## Next Steps

See the [Tutorial](../tutorial/index.md) page for a step-by-step guide on setting up a Fides data privacy workflow.
