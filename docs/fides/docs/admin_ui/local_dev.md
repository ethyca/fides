# Admin UI

Fides provides a built-in control panel for managing policies, system users, and datastore connections.

## Developing Locally

For testing and local development, clone the [Fides repository](https://github.com/ethyca/fides/).

### Creating the root user

In the top-level `fides` directory, run `nox -s user`.

A series of prompts will walk you through creating a username and password. Passwords require 8 or more characters, upper and lowercase characters, a number, and a symbol. 

This will create an Admin UI Root User that can be used to access the local UI, and additional [user endpoints](./user_management.md#managing-users-from-the-api).

### Accessing the Control Panel

From the root `fides` directory, run the following:
``` sh
    nox -s admin_ui
```

This will install the necessary dependencies, and run the development environment.

Visit `http://localhost:3000/` in your browser, and provide user credentials to log in. 