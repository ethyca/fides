# Contributing to FidesOps

Welcome to the contribution guidelines for Ethyca's FidesOps system. Please follow these as best you can when contributing new code.

## Database -- Postgres

FidesOps uses a local database to store application context. This database in configured in `docker-compose.yml` as a Postgres SQL instance. Connection details for this instance can be provided inside `.env.dev` or inside the config class in `src/app/core/config.py`, and will be automatically detected by Alembic when generating and running migrations.

Running the database will happen automatically when you run `make compose-build`. The database can also be initialised manually inside a `make server-shell` by running

```bash
cd src
alembic upgrade head
```

NB. Although we use Postgres, this can be overriden using the `SQLALCHEMY_DATABASE_URI` environment variable to point to any SQLAlchemy compatible system, so we should avoid using any Postgres-specific features until absolutely necessary.


### The ORM -- SQLAlchemy

SQLAlchemy is an Object Relational Mapper, allowing us to avoid writing direct database queries within our codebase, and access the database via Python code instead. The ORM provides an additional configuration layer allowing user-defined Python classes to be mapped to database tables and other constructs, as well as an object persistence mechanism known as the `Session`. Some common uses cases are listed below, for a more comprehensive guide see: https://docs.sqlalchemy.org/en/14/tutorial/index.html


### Adding models

Database tables are defined with model classes. Model files should live in `src/app/models/`. Individual model classes must inherit from our custom base class at `app.db.base_class.Base` to ensure uniformity within the database. Multiple models per file are encouraged so long as they fit the same logical delineation within the project. An example model declaration is added below. For a comprehensive guide see: https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#declarative-mapping

```
class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    page_count = Column(Integer, nullable=True)
    author_id = Column(Integer, ForeignKey("author.id"), nullable=False)
```
When models are added to the project, we must then add them to the database in a recordable and repeatable fashion using migrations.


### Using Alembic migrations

Some common Alembic commands are listed below. For a comprehensive guide see: https://alembic.sqlalchemy.org/en/latest/tutorial.html. The commands will need to be run inside a shell on your Docker containers, which can be opened with `make server-shell`.

In the `/src` directory:

- Migrate your database to the latest state: `alembic upgrade head`
- Automatically generate a new migration: `alembic revision --autogenerate -m "<a message describing your changes>"`
- Create a new migration file to manually fill out: `alembic revision -m "<a message describing your changes>"`
- Migrate your database to a specific state `alembic upgrade <revision-id>` or `alembic downgrade <revision-id>`, (or if you want to be smart `alembic upgrade <revision-id> || alembic downgrade <revision-id>` is handy when you don't know whether the target revision is an upgrade or downgrade)
  - NB. You can find the `revision-id` inside each migration file in `alembic/versions/` on line 3 next to `Revision ID: ...`

NB. These Alembic commands will need to be run on your application's database. If you are using Docker this means you need to SSH into your Docker container to run the command via `make server-shell`. An offshoot of this is that when the migration files are created, they'll be added to the Docker container's `alembic/versions/` dir but not necessarily to your local dir (which is where you'll likely be running `git` commands from). For the time being a workaround for this is to copy the migration file inside your Docker container, and replicate that exact file again on your local file system.


### Using the database via models

Once you've added database tables via project models, you're ready to read, write and update them via Python code. Some examples of common use cases here are listed below. Official documentation is here: https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.

- Import our application's database session: `from fidesops.db.session import get_db_session`
- Instantiate the database interaction object:
```
SessionLocal = get_db_session()
db = SessionLocal()
```
- Create a new row in a table:
```
db_obj = User(
    email="admin@fidesops.app",
    full_name="FidesOps Admin",
    is_superuser=True,
    is_active=True,
)
db.add(db_obj)
db.commit()
db.refresh(db_obj)
```
- Fetch all objects in a table: `users = db.query(User).all()`
- Fetch all objects in a table that meet some criteria: `active_users = db.query(User).filter(User.is_active == True)`
- Get a specific row in a table: `user = db.query(User).get(User.email == "admin@fidesops.app")`
- Update a specific row in a table:
```
user.email = "updated@fidesops.app"
db.add(user)
db.commit()
db.refresh()
```

### Connecting to the database
When you run `make server` or `make server-shell`, the database will be spun up in a Docker container with port `5432` exposed on localhost. You can connect to it using the credentials found in `.env.dev`, e.g.

- Hostname: `localhost`
- Port: `5432`
- Username: see `POSTGRES_USER` in `.env.dev`
- Password: see `POSTGRES_PASSWORD` in `.env.dev`


## Tests -- Pytest

Tests are run using `pytest`. Some commands you may need are listed below. The full documentation can be found at: https://docs.pytest.org/en/6.2.x/. There is some additional Pytest config in the `pyproject.toml` file at the root of the repo. Running `make pytest` will automatically migrate the database for you to the latest version by running `alembic upgrade head` before the `pytest` command itself.

- Run all tests: `make pytest`
- Run all tests in a directory: `make pytestpath=path/to/dir/ pytest`
- Run all tests in a file: `make pytestpath=path/to/file.py pytest`
- Run all tests within a class within a file: `make pytestpath=path/to/file.py::ClassName pytest`
- Run a specific test within a class within a file: `make pytestpath=path/to/file.py::ClassName::method_name pytest`
- Run a specific test within a file: `make pytestpath=path/to/file.py::method_name pytest`
- Run integration tests (access): `make pytest-integration-access`
- Run integration tests (erasure): `make pytest-integration-erasure`


### How to write tests

Tests should be written into files nested under the `tests/` directory in the project's root. The file structure should reflect that of the code in `src/app/`. For example, tests for `src/app/api/api_v1/endpoints/login/` are located in `tests/api/api_v1/test_login.py`. Below are outlined some common functions you'll find useful when writing tests.

- Make an API call:
```
def test_some_api_endpoint(client: TestClient) -> None:
    data = {
        "some": "data"
    }
    r = client.post("/api/v1/endpoint/, data=data)
```
- Make an assertion: `assert r.status_code == 200`
- Mock any object:
```
from unittest.mock import patch
from fidesops.module import ClassName
@patch('app.module.ClassName')
def test_something(mock_classname):
    ClassName()
    assert ClassName.called
```
More info. on mocking can be found in the unittest.mock docs here: https://docs.python.org/3/library/unittest.mock.html
- Test for multiple edge cases with `parameterize`:
```
import pytest

@pytest.mark.parametrize("a,b,expected", [
    ("a", "b", "ab"),
    ("cd", "e", "cde"),
])
def test_concatenate_chars(a, b, expected):
    result = concatenate(a, b)
    assert result == expected
```
This will run `test_concatenate_chars("a", "b", "ab")` then `test_concatenate_chars("cd", "e", "cde")`
- Load test fixtures: TBC


## Exception Handling

Our preference for exception handling is by overriding the nearest sensible error, for example:

```
class SomeException(ValueError):
    "a docstring"


def some_method():
    raise SomeException("a message")
```


## API URLs

We define API URLs for specific API versions as constants within `app.api.v1.urn_registry` (where `v1` can be substituted for that particular API version), then import those URLs into their specific API views. Since we are on the first version, there is no clear precedent set for overriding URLs between versions yet. The most likely change is that we'll override the `APIRouter` class instantiation with a different base path (ie. `/api/v2` instead of `/api/v1`). For example:

```
PRIVACY_REQUEST = "/privacy-request"
PRIVACY_REQUEST_DETAIL = "/privacy-request/{privacy_request_id}"
```

would both resolve as `/api/v1/privacy-request` and `/api/v1/privacy-request/{privacy_request_id}` respectively.


## PR Merging Guidelines

Pull requests should be submitted with a clear description of the issue being handled, including links to any external specifications, JIRA tickets or Github issues. PRs should not be merged by the person submitting them, except in rare and urgent circumstances.


## Linting -- Pylint

Linting is done using the Pylint library. Full docs can be found here: https://docs.pylint.org/en/1.6.0/tutorial.html. Our Pylint rules are configured inside `pyproject.toml`.

- Run project linting with: `make pylint`


## Autoformatting -- Black

Black is used to autoformat the repo's code. Full docs can be found here: https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html. Our Black rules are configured inside `pyproject.toml`/

- Run autoformatting with: `make black`


## Type checking -- Mypy

Mypy is used to enforce static typechecking at compile time. Full docs can be found here: https://mypy.readthedocs.io/en/stable/config_file.html. Our Mypy rules are configured inside `mypy.ini`.

- Run type checking with: `make mypy`


NB. pre-commit checks can be run with `make check-all`.


## General debugging -- pdb

The project uses `pdb` for debugging as a `dev-requirement`. You can set breakpoints with `pdb` in much the same way you'd set them using `debugger` in Javascript. Insert `import pdb; pdb.set_trace()` into the line where you want the breakpoint to set, then run your Python code.


## Docker

The project is based on Docker Compose. To further inspect the commands we generally use you can read `Makefile` in the root of this repo.

### Clearing local Docker instances

Occasionally when developing you'll run into issues where it's beneficial to remove all existing Docker instances in order to recreate them based on some updated spec. Some commands to do this are below:

  - Stop all running containers: `docker-compose down`
  - Delete all local containers: `docker rm -f $(docker ps -a -q)`
  - Delete all local Docker volumes: `docker volume rm $(docker volume ls -q)`
  - Remove temp. files and installed dependencies: `make clean`
  - Delete all stopped containers, all networks not used by a container, all dangling images, and all build cache: `docker system prune`
  - Recreate the project: `make compose-build`
