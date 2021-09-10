# Development Overview

---

Thanks for contributing to Fides! This section of the docs is designed to help you become familiar with how we work, the standards we apply, and how to ensure your contribution is successful.

If you're stuck, don't be shy about asking for help [on GitHub](https://github.com/ethyca/fides/issues).

## Getting Started

### Clone Fides

To clone Fides for development, run `git clone https://github.com/ethyca/fides`.

Once that is complete, there are a few different ways to spin up the project and get coding!

* __Recommended__: If you're using VS Code, the recommended way to work on Fides is by leveraginng the Dev Container feature. The repo has a `.devcontainer/devcontainer.json` file already included that will set up a complete environment in VS Code, including the suggested VS Code extensions and settings.
* If you're using an editor besides VS Code, then the next best way to work on Fides is by utilizing the `Makefile` commands. See the guide [here](https://github.com/ethyca/fides/blob/main/docs/fides/docs/getting_started/docker.md) for more information on getting setting up via the `Makefile`.

### Write your code

We have no doubt you can write amazing code! However, we want to help you ensure your code plays nicely with the rest of the Fides ecosystem. Many projects describe code style and documentation as a suggestion; in Fides it's a CI-checked requirement.

* To learn how to style your code, see the [style guide](code_style.md).
* To learn how to document your code, see the [docs guide](documentation.md).
* To learn how to test your code, see the [tests guide](testing.md).
* To learn what format your PR should follow, make sure to follow the [pull request guidelines](pull_requests.md).

### Submit your code

In order to submit code to Fides, please:

* [Fork the Fides repository](https://help.github.com/en/articles/fork-a-repo)
* [Create a new branch](https://help.github.com/en/desktop/contributing-to-projects/creating-a-branch-for-your-work) on your fork
* [Open a Pull Request](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) once your work is ready for review
* Once automated tests have passed, a maintainer will review your PR and provide feedback on any changes it requires to be approved. Once approved, your PR will be merged into Fides.

### Congratulations

You're a Fides contributor - welcome to the team! 🎉
