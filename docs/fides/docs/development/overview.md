# Development Overview

Thank you for your interest in contributing to Fides! This section of our documentation is designed to help you become familiar with how we work, the standards we apply, and how to ensure your contribution is successful.

If you're stuck, don't be shy about asking for help [on GitHub](https://github.com/ethyca/fides/issues).

## Getting Started

The first step is to clone the Fides repo for development if you haven't already:

```bash
git clone https://github.com/ethyca/fides
```

Once that's complete, there are a few different tools to install for get everything up and running.

---

## Requirements

The primary requirements for contributing to Fides are `Docker` and `Python`. The download links as well as minimum required versions are provided below

 _NOTE: Installing these requirements via Brew or other package managers is highly discouraged. Please use the provided links for a more stable experience._

* __Docker Desktop (version 20.10.11 or later)__ - [Docker Desktop Download Page](https://www.docker.com/products/docker-desktop/)
* __Python (version 3.9 through 3.10)__ - To simplify the installation experience and create a more stable Python installation that can be managed indepently, we recommend installing Python via Anaconda. The installer for Anaconda can be found [here](https://www.anaconda.com/download).

!!! warning
    _Mac Users_: Apple's ARM silicon (M-series chips, i.e. M1, M2, M2 Max, etc.) have a few extra requirements to get Fides running

### Additional Requirements for Mac Users (ARM-based)

Install FreeTDS and OpenSSL

```bash
brew install freetds openssl
```

Add the following to your run commands (i.e. `.zshrc`), updating any path/versions to match yours

```bash
export LDFLAGS="-L/opt/homebrew/Cellar/freetds/1.3.18/lib -L/opt/homebrew/Cellar/openssl@1.1/1.1.1u/lib"
export CFLAGS="-I/opt/homebrew/Cellar/freetds/1.3.18/include"
```

### Optional Requirements for Mac Users (ARM-based)

Explicitly set resource allocations in Docker Desktop

* CPUs: 4
* Memory:8GB
* Disk Limit: 200GB

Now that those are installed, the final step is to install the Python dev requirements for the Fides project. We recommend doing this in a virtual environment.

```bash
pip install -r dev-requirements.txt
```

---

### Write your code

We have no doubt you can write amazing code! However, we want to help you ensure your code follows the style and patterns of Fides and has the highest chance possible to be accepted. Many projects describe code style and documentation as a suggestion; in Fides it's a CI-checked requirement.

* To learn how to develop new features or fix bugs, see the [developing Fides](developing_fides.md) page.
* To learn how to style your code, see the [style guide](code_style.md).
* To learn how to document your code, see the [docs guide](documentation.md).
* To learn how to test your code, see the [tests guide](testing.md).
* To learn what format your PR should follow, make sure to follow the [pull request guidelines](pull_requests.md).

### Submit your code

In order to submit code to Fides, please:

* [Fork the Fides repository](https://help.github.com/en/articles/fork-a-repo)
* [Create a new branch](https://help.github.com/en/desktop/contributing-to-projects/creating-a-branch-for-your-work) on your fork
* [Open a Pull Request](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) once your work is ready for review
* Once automated tests have passed, a maintainer will review your PR and provide feedback on any changes it requires to be approved.
* Once approved, your PR will be merged into Fides and included in a future release.

### Congratulations

You're a Fides contributor - welcome to the team! 🎉
