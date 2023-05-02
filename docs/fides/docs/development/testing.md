# Testing

Fides loves tests! There are a few important reasons to write tests:

- **Make sure your code works**

  Tests ensure that your code does the thing you intend it to do.

  If you have a function that adds two numbers, you'll want to test that it does, in fact, return their sum. If behavior depends on a configuration setting, ensure that changing that setting changes the behavior. In short, if you wrote a line of code, you should test that line works as expected.

- **Make sure your code doesn't not work**

  It may seem silly, but another important reason to write tests is to ensure that your code behaves as expected _even when it's broken_.

  This is especially important for a project like Fides, which is focused on helping engineers when something unexpected happens to their code. For example, you could write tests about what you expect to happen if your function is called with incorrect (or no) arguments, or to ensure that any errors are properly trapped and handled.

- **Tests are documentation**

  Ultimately, your tests are the best documentation for your code.

  Another developer should be able to look at your tests and understand what your code does, how to invoke it, and what edge cases it contains. Therefore, try to write short, self-explanatory tests with descriptive titles.

- **Help future developers**

  As Fides grows, your code will be reused in more and more places, by developers who may not be familiar with the details of your implementation. Therefore, your tests are an opportunity to ensure that your code is used correctly in the future.

  For example, if your code needs to be used in a certain way, or expects a certain configuration, or is always expected to return a certain output, or has any other details that might impact its ability to be used in the framework, write a test for it! At minimum, you'll help a future developer understand that you consciously chose to design your code a certain way.

## Writing tests

Fides' tests are stored in the `tests` directory.

Tests should have descriptive names that make it clear what you're testing. If necessary, add a docstring or comment to explain why you're testing this specific thing.

```python
# Good test name
def test_dry_evaluate_system_fail(server_url, resources_dict):
    ...

# Bad test name
def test_dry_evaluate():
    ...
```

Fides has a few [`pytest` fixtures](https://docs.pytest.org/en/stable/fixture.html) available for testing; see `conftest.py` for details.

### Integration tests vs. mocked tests

Generally, tests that include mocking are discouraged. Mocking can create a false sense of security and obfuscate possible errors in the code that only present themselves when integration tested.

## Running tests

Given the relative complexity of the setup around Fides and reliance on Docker, test commands should usually be run in a shell or via Nox sessions. The following subsections describe how to execute both.

### Running Tests in a Shell

As described in [Developing Fides](developing_fides.md), we'll be running these tests from within a shell. As a reminder, spinning up Fides and opening a shell requires the following commands:

1. `nox -s dev`
1. Once the webserver is running from the previous command, open a new terminal and run `nox -s shell`

You're now ready to start testing!

#### Invoking Pytest

Fides uses `pytest` for unit testing. Let's collect all of the available tests to verify pytest is working as expected:

```bash
# Collects all available tests without running anything
pytest --collect-only
```

#### Running specific tests

To run a subset of tests, provide a filename or directory; to match a specific test name, use the `-k` flag:

```bash
# Run all tests in the tests/ctl/ directory that contain the word "api" in their name
pytest tests/ctl/ -k api
```

The `--sw` flag will exit `pytest` the first time it encounters an error; subsequent runs with the same flag will skip any tests that succeeded and run the failed test first.

For more information on available Pytest invocation options, see the documentation [here](https://docs.pytest.org/en/6.2.x/usage.html#usage-and-invocations).

#### Excluding tests

Some tests also test integration with external services like Snowflake which require both internet access and authentication credentials. It is possible to skip these tests by excluding tests with the `external` mark.

```bash
# Run all tests except for external ones
pytest -m "not external"
```

This is far from the only mark used in the test suite however. To see a full list, they are all documented in the `[tool.pytest]` section of the [pyproject.toml](https://github.com/ethyca/fides/blob/main/pyproject.toml).

### Running Test Suites via Nox

To run tests in a more robust and repeatable way, Nox also has extensive commands for running tests packaged with various marks and infrastructure. However, it is important to note that these commands are not designed for rapid iteration and TDD in mind, but instead for maximum reproducability. To run tests in a more TDD-style, see the section [Running Tests in a Shell](#running-tests-in-a-shell).

Additionally, these are the exact same Nox sessions that are run in CI. Thus if you are seeing CI failures and are trying to reproduce or remediate them, it is recommended to run those failing tests locally via these Nox sessions as the results will generally always be the same.

#### Building the Test Image

The Nox test sessions assume that all of the required images have already been built. To build the Fides image used for testing, run the following command:

```bash
nox -s "build(test)"
```

Once that is complete, you're ready to start running test sessions.

#### Test Sessions

The following table describes each pytest-related session:

| Session (with Param) | Mark(s) | Test Path | Requires Credentials? | Description |
| :---: | :---: | :---: | :---: | :---: |
| pytest(ctl-unit) | unit | tests/ctl | No |Simplest set of `ctl` tests Should generally avoid the webserver but not guaranteed. |
| pytest(ctl-integration) | integration | tests/ctl | No | Tests that are known to require the webserver. |
| pytest(ctl-not-external) | not external | tests/ctl | No | Tests unit/integration but without touching external resources. |
| pytest(ctl-external) | external | tests/ctl | Yes | Tests that require external resources such as Snowflake or BigQuery. |
| pytest(ops-unit) | not integration and not integration_external and not integration_saas | tests/ops | No | As there is no "unit" tag within the ops tests, it is instead achieved via numerous "not" marks. |
| pytest(ops-integration) | N/A | N/A | No | This is a special test case, as the handling of test running is done by `run_infrastructure.py`. More information and logic can be found there. |
| pytest(ops-external-datastores) | integration_external | tests/ops | Yes | Runs tests that connect to external datastores such as Snowflake. |
| pytest(ops-saas) | integration_saas | tests/ops | Yes | Runs tests related to the `connectors` code. Spins up additional local resources and connects to outside resources. |
| pytest(lib) | N/A | tests/lib | No | Test `lib` module functionality. |
| pytest(nox) | N/A | tests/nox | No | Tests functionality related to the nox session. |

!!! note
    For additional information, you can view the source file [test_setup_nox.py](https://github.com/ethyca/fides/blob/main/noxfiles/test_setup_nox.py) that contains all of the code that runs these tests.

## Testing Environment

### Quickstart

1. Use `nox -s "fides_env(test)"` to launch the test environment
2. Read the terminal output for details
3. Customize Fides ENV variables by editing `.env`

### Overview

To facilitate thorough manual testing of the application, there is a comprehensive testing environment that can be set up via a single `nox` command: `nox -s "fides_env(test)"`.

This test environment includes:

* Fides Server
* Fides Admin UI
* Fides Postgres Database & Redis Cache
* Sample "Cookie House" Application
* Test Postgres Database
* Test Redis Database
* Sample Resources
* Sample Connectors
* etc.

This test environment is exactly the same environment that users can launch themselves using `fides deploy up`, and you can find all the configuration and settings in `src/fides/data/sample_project`.

### Configuration

There are two ways to configure the `fides` server and CLI:

1. Editing the ENV file in the project root: `.env`
2. Editing the TOML file in the sample project files: `src/fides/data/sample_project/fides.toml`

The `.env` file is safest to add secrets and local customizations, since it is `.gitignore`'d and will not be accidentally committed to version control.

The `fides.toml` file should be used for configurations that should be present for all users testing out the application.

### Advanced Usage

The environment will work "out of the box", but can also be configured to enable other features like S3 storage, email notifications, etc.

To configure these, you'll need to edit the `.env` file and provide some secrets - see `example.env` for what is supported.

### Automated Cypress E2E Tests

The test environment is also used to run automated end-to-end (E2E) tests via Cypress. Use `nox -s e2e_test` to run this locally.
