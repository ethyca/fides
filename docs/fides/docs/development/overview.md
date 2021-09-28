# Development Overview

---

Thanks for contributing to Fidesctl! This section of the docs is designed to help you become familiar with how we work, the standards we apply, and how to ensure your contribution is successful.

If you're stuck, don't be shy about asking for help [on GitHub](https://github.com/ethyca/fides/issues).

## Getting Started

The first step is to clone the Fidesctl repo for development:

```bash
git clone https://github.com/ethyca/fides
```

Once that's complete, there are a few different ways to spin up the project and get coding!

### Developer Workflows

There are a few different ways to develop Fidesctl, they are listed below _in order of how strongly they are recommended!_

1. If you're using VS Code, the recommended way to work on Fidesctl is by leveraging the Dev Containers feature. The repo has a `.devcontainer/devcontainer.json` file already included that will set up a complete environment in VS Code, including the suggested VS Code extensions and settings. Follow these steps to get started:
    1. Install the `Remote-Containers` extension for VS Code.
    1. Open the command window (the F1 key will open it, by default) and select the `Remote-Containers: Open Folder in Container...` command.
    1. Click "Open", without having selected any specific folder.
    1. The containers will now spin up and VS Code will be running inside of the containers. The bottom left of the IDE will now say `Dev Container: Fidesctl`.
    1. When you open a new VS Code shell, it will be inside of the `fidesctl` container, and you'll have access to all of the `fidesctl` commands as well as any Python commands like `pytest`, `black`, `mypy`, etc.
1. If you're using an editor besides VS Code, then the next best way to work on Fidesctl is by utilizing the `Makefile` commands:
    1. See the guide [here](../getting_started/docker.md) for more information on getting set up via the `Makefile`
    1. Once you've gotten everything set up, run `make cli` to spin up a shell within the `fidesctl` container.
    1. You can and should run all of your various development commands from within this shell, such as `pytest`, `black`, etc.
1. Finally, the least-recommended method would be to install the project in your local environment and develop directly.

### Write your code

We have no doubt you can write amazing code! However, we want to help you ensure your code plays nicely with the rest of the Fidesctl ecosystem. Many projects describe code style and documentation as a suggestion; in Fidesctl it's a CI-checked requirement.

* To learn how to style your code, see the [style guide](code_style.md).
* To learn how to document your code, see the [docs guide](documentation.md).
* To learn how to test your code, see the [tests guide](testing.md).
* To learn what format your PR should follow, make sure to follow the [pull request guidelines](pull_requests.md).

### Submit your code

In order to submit code to Fidesctl, please:

* [Fork the Fidesctl repository](https://help.github.com/en/articles/fork-a-repo)
* [Create a new branch](https://help.github.com/en/desktop/contributing-to-projects/creating-a-branch-for-your-work) on your fork
* [Open a Pull Request](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) once your work is ready for review
* Once automated tests have passed, a maintainer will review your PR and provide feedback on any changes it requires to be approved. Once approved, your PR will be merged into Fidesctl.

### Congratulations

You're a Fidesctl contributor - welcome to the team! 🎉
