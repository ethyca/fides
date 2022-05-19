# Admin UI

Instructions on running the Admin UI and generating users for local development.

## Running Locally

To get started locally, clone the [FidesOps repository](https://github.com/ethyca/fidesops/), and ensure you have [Node.js](https://nodejs.org/en/download/) installed to run the application.
### Creating the root user

In the top-level `fidesops` directory, run `make user`.

A series of prompts will walk you through creating a username and password. Passwords require 8 or more characters, upper and lowercase characters, a number, and a symbol. 

This will create an Admin UI Root User that can be used to access additional [user endpoints](#managing-users).

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
