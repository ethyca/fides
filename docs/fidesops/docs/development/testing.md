# Testing

---

Fides loves tests! There are a few important reasons to write tests:

- **Make sure your code works when it's supposed to**

  Tests ensure that your code does the thing you intend it to do.

  If you have a function that adds two numbers, you'll want to test that it does, in fact, return their sum. If behavior depends on a configuration setting, ensure that changing that setting changes the behavior. In short, if you wrote a line of code, you should test that line works as expected.

- **Make sure your code doesn't work when it's not supposed to**

  It may seem silly, but another important reason to write tests is to ensure that your code behaves as expected _even when it's broken_.

  This is especially important for a project like Fides, which is focused on helping engineers when something unexpected happens to their code. For example, you could write tests about what you expect to happen if your function is called with incorrect (or no) arguments, or to ensure that any errors are properly trapped and handled.

- **Tests are documentation**

  Ultimately, your tests are the best documentation for your code.

  Another developer should be able to look at your tests and understand what your code does, how to invoke it, and what edge cases it contains. Therefore, try to write short, self-explanatory tests with descriptive titles.

- **Help future developers**

  As Fides grows, your code will be reused in more and more places, by developers who may not be familiar with the details of your implementation. Therefore, your tests are an opportunity to ensure that your code is used correctly in the future.

  For example, if your code needs to be used in a certain way, or expects a certain configuration, or is always expected to return a certain output, or has any other details that might impact its ability to be used in the framework, write a test for it! At minimum, you'll help a future developer understand that you consciously chose to design your code a certain way.

---

## Writing tests

Fides's tests are stored in the `tests` directory.

Tests should have descriptive names that make it clear what you're testing. If necessary, add a docstring or comment to explain why you're testing this specific thing.

```python
def test_dry_evaluate_system_fail(server_url, resources_dict):
    ...

# bad test name
def test_dry_evaluate():
    ...
```

Fidesops has a few [`pytest` fixtures](https://docs.pytest.org/en/stable/fixture.html) available for testing; see `conftest.py` for details.

## Running tests

Fidesops uses `pytest` for unit testing. As with other `make` commands, you have the option to run `pytest` in command-line or in application shell:

1. In shell: Once in the fidesops container shell (`make server-shell`, or `make integration-shell` if running integration tests), invoke `pytest` from the root fidesops directory:

```bash
cd fidesops
pytest
```

2. From regular command-line:

```bash
make pytest
```

### Running specific tests

To run a subset of tests, provide a filename or directory; to match a specific test name, use the `-k` flag:

```bash
# run all tests in the tests/ops/integration directory that contain the word "api" in their title
pytest tests/ops/integration/ -k api
```

Other commands you may need are listed below. The full documentation can be found at: <https://docs.pytest.org/en/6.2.x/>.

- Run all tests in a directory: `make pytestpath=path/to/dir/ pytest`
- Run all tests in a file: `make pytestpath=path/to/file.py pytest`
- Run all tests within a class within a file: `make pytestpath=path/to/file.py::ClassName pytest`
- Run a specific test within a class within a file: `make pytestpath=path/to/file.py::ClassName::method_name pytest`
- Run a specific test within a file: `make pytestpath=path/to/file.py::method_name pytest`
- Run integration tests (access): `make pytest-integration`
- Run integration tests (erasure): `make pytest-integration-erasure`

#### Debugging

For debugging, we recommend installing the [`pdbpp`](https://github.com/pdbpp/pdbpp) package and running `pytest` with the `--pdb` flag (which will open the debugger on any error) or setting `breakpoint()` appropriately.

#### Stepwise execution

The `--sw` flag will exit `pytest` the first time it encounters an error; subsequent runs with the same flag will skip any tests that succeeded and run the failed test first.

## CI Workflows

CI will run automatically against any PR you open. Please run your tests locally first to avoid "debugging in CI", as this takes up resources that could be used by other contributors.
