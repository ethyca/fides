# Admin UI

Fidesctl provides a built-in control panel for managing policies, system users, and datastore connections.

[admin ui]

## Developing Locally

For testing and local development, clone the [Fides repository](https://github.com/ethyca/fides/), and ensure you have [Node.js](https://nodejs.org/en/download/) installed to run the application.

### Creating the root user

In the top-level `fides` directory, run `make user`.

A series of prompts will walk you through creating a username and password. Passwords require 8 or more characters, upper and lowercase characters, a number, and a symbol. 

This will create an Admin UI Root User that can be used to access the local UI, and additional [user endpoints](./user_management.md#managing-users-from-the-api).

### Accessing the Control Panel

From the root `fidesops` directory, run the following:
``` sh
    cd clients/admin-ui
    npm install
    npm run dev
```

This will navigate you to the `admin-ui` directory, and run the development environment.

Visit `http://localhost:3000/` in your browser, and provide user credentials to log in. 

!!! tip "While your [Root Account](#creating-the-root-user) can be used to access the UI, additional [endpoints](#managing-users) are available to create and manage individual users for production-grade deployments."


## Production Deployments 