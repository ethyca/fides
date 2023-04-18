# Developing Fides

The primary developer interface for Fides is via a tool called Nox. Nox is a pure-Python replacement for tools like `make`. You can read more about Nox in the official documentation [here](https://nox.thea.codes/en/stable/index.html).

Additionally, much of what `nox` helps abstract is related to Docker. This usually makes it possible to troubleshoot potential `nox` issues by using various Docker commands directly.

## Terminology

For the purposes of this documentation, there is some Nox-terminology that is helpful to understand first.

* `posarg` - This refers to a _Positional Argument_. These can be provided to _any_ Nox command by putting `--` at the end of a command followed by the argument that you would like to provide. For instance `nox -s dev -- shell`
* `session` - This is the equivalent of a single command, or a `target` in Make. They can be chained together arbitrarily, and the order of execution will be preserved. For example `nox -s isort black`
* `param` - This is a specified value that is provided directly to a session. For instance `nox -s "isort(<param>)"`. Note that due to terminal limitations, the `session` + `param` must be wrapped in quotes for proper escaping. Additionally, if a `session` has multiple params but none are specific, all permutations of that session will be run.

## General Commands to Know

While there are many sessions available in our `nox` setup, there are a few that are generally useful to know when trying to familiarize yourself with the development environment or introspect.

| Command | Example | Description |
| :-----: | :-----: | :---------: |
| `nox` | N/A | This is the default session that runs when no other session is provided. Automatically opens this page. |
| `nox -l`| N/A | Provides a list of all available `nox` sessions. |
| `nox -s usage -- <command>` | `nox -s usage -- dev` | Shows the full docstring for a single session. The name of the session is provided as a positional argument. |

## Getting Started

Given that the majority of commands rely on Docker images, the first step is going to be getting some Docker images built. This is handled by the `build` session. Check the docs with the `usage` session:

```sh
nox -s usage -- build
```

The simplest way to build everything is to run `nox -s build`. This will build all available Docker images used for development and testing. Additionally, to build only a specific image(s), run `nox -s usage -- build` to see what params have been documented.

## Verifying Your Changes

Once you've made some changes, it's time to verify that they are working as expected.

## Running Tests

This is a discrete section because unless following strict [TDD](https://en.wikipedia.org/wiki/Test-driven_development), there will probably be some manual verification done before moving on to testing.

## Static Checks

For the sake of simplicity, all of the typical pre-commit static checks are packaged into a single session:

`nox -s static_checks`

This installs and runs the various checks in their own virtual environment for maximum consistency.
