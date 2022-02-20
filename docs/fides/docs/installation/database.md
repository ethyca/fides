# Setting up the database

The fidesctl webserver is the only part of the application that touches the fidesctl database directly. It will automatically run migrations and seed the database with the default taxonomy on startup.

If needed, you can also run `fidesctl db init` or `fidesctl db reset` via the CLI, which will tell the webserver to execute those actions, although these should not be needed under normal circumstances.
