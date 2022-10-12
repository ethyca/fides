# Testing Environment

To facilitate thorough manual testing of the application, there is a comprehensive testing environment that can be set up via a single `nox` command.

Running `nox -s test_env` will spin up a comprehensive testing environment that does the following:

1. Builds the Webserver, Admin UI and Privacy Center.
1. Uses the `run_infrastructure.py` script to run the interactive quickstart as well as seed additional test data.
1. Spins up the entire application, including all external Docker-based datastores as well as UIs.
1. Loads the `ctl`-related demo resources
1. Opens a shell within the webserver Docker container, with the CLI available for use

With those steps completed, the following aspects can be tested:

* The API, either by visiting the API docs at `localhost:8080/docs` or making requests directly
* The CLI, using `fides` as the entrypoint within the shell
* The Privacy Center, available at `localhost:3001`
* The Admin UI, available at `localhost:3000` with `?` and `?` as the username and password respectively.
