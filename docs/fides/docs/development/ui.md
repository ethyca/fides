
## Local Development

To test the UI locally, clone the [FidesOps repository](https://github.com/ethyca/fidesops/), and ensure you have [Node.js](https://nodejs.org/en/download/) installed to run the application.

### Creating the root user

A root user can be created by adding a `root_username` and `root_password` to the
security section of `fidesops.toml` file, or by setting `FIDESOPS__SECURITY__ROOT_USERNAME`
and `FIDESOPS__SECURITY__ROOT_PASSWORD` environment variables.

This will allow you to login in with a root user that can be used to access
additional [user endpoints](#managing-users).

### Accessing the Control Panel

From the root `fidesops` directory, run the following:

``` sh
    cd clients
    npm install
    cd admin-ui
    turbo run dev
```

This will navigate you to the `admin-ui` directory, and run the development environment.

Visit `http://localhost:3000/` in your browser, and provide your user credentials to log in.

## Authentication

To enable stable authentication you must supply a `NEXTAUTH_SECRET` environment
variable. The best way to do this is by creating a `.env.local` file, which Next
will automatically pick up:

```bash
echo NEXTAUTH_SECRET=`openssl rand -base64 32` >> .env.local
```

## Backend deployment

Fidesops automatically serves a version of the UI when running `nox -s dev`.

To deploy a full version of the UI from a backend, run the following from the root fidesops directory:

```sh
    cd clients
    npm install
    cd admin-ui
    turbo run prod-export
```

This will build and place the Admin UI files into a location accessible by backend fidesops deployments.

To test the UI, run `nox -s dev` from the root directory, and visit `http://0.0.0.0:8080/index.html`.
