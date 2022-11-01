# Contributing Details

## API Endpoints

### Postman API collection

The [fides Postman Collection](./postman/Fides.postman_collection.json)) can be used to test a variety of privacy request endpoints. Follow the [Using Postman](./postman/using_postman.md) guide to learn more about the how to use the collection.

### API URLs

We define API URLs for specific API versions as constants within `fides.api.ops.api.v1.urn_registry` (where `v1` can be substituted for that particular API version), then import those URLs into their specific API views. Since we are on the first version, there is no clear precedent set for overriding URLs between versions yet. The most likely change is that we'll override the `APIRouter` class instantiation with a different base path (ie. `/api/v2` instead of `/api/v1`). For example:

```
PRIVACY_REQUEST = "/privacy-request"
PRIVACY_REQUEST_DETAIL = "/privacy-request/{privacy_request_id}"
```

would both resolve as `/api/v1/privacy-request` and `/api/v1/privacy-request/{privacy_request_id}` respectively.

## Database and Models

### The ORM -- SQLAlchemy

SQLAlchemy is an Object Relational Mapper, allowing us to avoid writing direct database queries within our codebase, and access the database via Python code instead. The ORM provides an additional configuration layer allowing user-defined Python classes to be mapped to database tables and other constructs, as well as an object persistence mechanism known as the `Session`. Some common uses cases are listed below, for a more comprehensive guide see: <https://docs.sqlalchemy.org/en/14/tutorial/index.html>

### Adding models

Database tables are defined with model classes. Model files should live in `src/app/models/`. Individual model classes must inherit from our custom base class at `app.db.base_class.Base` to ensure uniformity within the database. Multiple models per file are encouraged so long as they fit the same logical delineation within the project. An example model declaration is added below. For a comprehensive guide see: <https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#declarative-mapping>
You should also import your model in src/fides/api/ops/db/base.py so it is visible for alembic.

```
class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    page_count = Column(Integer, nullable=True)
    author_id = Column(Integer, ForeignKey("author.id"), nullable=False)
```

When models are added to the project, we must then add them to the database in a recordable and repeatable fashion using migrations.

### Using the database via models

Once you've added database tables via project models, you're ready to read, write, and update them via Python code. Some examples of common use cases here are listed below. Official documentation is here: <https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query>.

- Import our application's database session: `from fides.api.ops.db.session import get_db_session`
- Instantiate the database interaction object:

```
SessionLocal = get_db_session(config)
db = SessionLocal()
```

- Create a new row in a table:

```
db_obj = User(
    email="admin@fides.app",
    full_name="Fides Admin",
    is_superuser=True,
    is_active=True,
)
db.add(db_obj)
db.commit()
db.refresh(db_obj)
```

- Fetch all objects in a table: `users = db.query(User).all()`
- Fetch all objects in a table that meet some criteria: `active_users = db.query(User).filter(User.is_active == True)`
- Get a specific row in a table: `user = db.query(User).get(User.email == "admin@fides.app")`
- Update a specific row in a table:

```
user.email = "updated@fides.app"
db.add(user)
db.commit()
db.refresh()
```

### Connecting to the database

When you run `nox -s dev`, the database will spin up in a Docker container with port `5432` exposed on localhost. You can connect to it using the credentials found in `.fides.toml`, e.g.

- Hostname: `localhost`
- Port: `5432`
- Username: see `database.user` in `.fides.toml`
- Password: see `database.password` in `.fides.toml`

### Alembic migrations

Some common Alembic commands are listed below. For a comprehensive guide see: <https://alembic.sqlalchemy.org/en/latest/tutorial.html>.

The commands will need to be run inside a shell on your Docker containers, which can be opened with `nox -s dev -- shell`.

In the `/src/fides` directory:

- Migrate your database to the latest state: `alembic upgrade head`
- Get revision id of previous migration: `alembic current`
- Automatically generate a new migration: `alembic revision --autogenerate -m "<a message describing your changes>"`
- Create a new migration file to manually fill out: `alembic revision -m "<a message describing your changes>"`
- Migrate your database to a specific state `alembic upgrade <revision-id>` or `alembic downgrade <revision-id>`, (or if you want to be smart `alembic upgrade <revision-id> || alembic downgrade <revision-id>` is handy when you don't know whether the target revision is an upgrade or downgrade)
  - NB. You can find the `revision-id` inside each migration file in `alembic/versions/` on line 3 next to `Revision ID: ...`

When working on a PR with a migration, ensure that `down_revision` in the generated migration file correctly references the previous migration before submitting/merging the PR.

## Exception Handling

Our preference for exception handling is by overriding the nearest sensible error, for example:

```
class SomeException(ValueError):
    "a docstring"


def some_method():
    raise SomeException("a message")
```

## General debugging -- pdb

The project uses `pdb` for debugging as a `dev-requirement`. You can set breakpoints with `pdb` in much the same way you'd set them using `debugger` in Javascript. Insert `import pdb; pdb.set_trace()` into the line where you want the breakpoint to set, then run your Python code.

## Docker

Occasionally when developing you'll run into issues where it's beneficial to remove all existing Docker instances in order to recreate them based on some updated spec. Some commands to do this are below:

- Stop all running containers: `docker compose down`
- Delete all local containers: `docker rm -f $(docker ps -a -q)`
- Delete all local Docker volumes: `docker volume rm $(docker volume ls -q)`
- Remove temp. files, installed dependencies, all local Docker containers and all local Docker volumes: `nox -s clean`
- Delete all stopped containers, all networks not used by a container, all dangling images, and all build cache: `docker system prune`
- Recreate the project: `nox -s "build(dev)"`
