# Running Fidesctl locally (Standalone)

This method of running fidesctl requires zero dependencies outside of Python and a default pip installation of fidesctl. It is intended as the fastest possible quick start and is not designed for production-grade deployments.

In standalone mode most CLI commands will not work as they require webserver connectivity for persistence. Crucially though, the core evaluation functionality is still present. To run evaluations in standalone mode, use the `--local` flag, but note that the evaluation results won't be persisted.

For more information on running a full fidesctl installation, see the [Running Fidesctl locally (Full Installation)](local_full.md) or [Running Fidesctl in Docker](docker.md) pages.

## System Requirements

See the Python section of the [Prerequisites and Dependencies](../installation/prerequisites_dependencies.md) page for more information.

## Fidesctl Installation

The next step is to install fidesctl via pip with the required extras:

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
