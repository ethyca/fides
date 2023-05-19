# Frontend Development

## Admin UI

To test the UI locally, clone the [Fides repository](https://github.com/ethyca/fides/), and ensure you have [Node.js](https://nodejs.org/en/download/) installed to run the application.

### Creating the root user

A root user can be created by adding a `root_username` and `root_password` to the
security section of `fides.toml` file, or by setting `FIDES__SECURITY__ROOT_USERNAME`
and `FIDES__SECURITY__ROOT_PASSWORD` environment variables.

This will allow you to login in with a root user that can be used to access
additional [user endpoints](#managing-users).

### Accessing the Control Panel

From the root `fides` directory, run the following:

``` sh
    cd clients
    npm install
    cd admin-ui
    turbo run dev
```

This will navigate you to the `admin-ui` directory, and run the development environment.

Visit `http://localhost:3000/` in your browser, and provide your user credentials to log in.

### Authentication

To enable stable authentication you must supply a `NEXTAUTH_SECRET` environment
variable. The best way to do this is by creating a `.env.local` file, which Next
will automatically pick up:

```bash
echo NEXTAUTH_SECRET=`openssl rand -base64 32` >> .env.local
```

### Backend deployment

Fides automatically serves a version of the UI when running `nox -s dev`.

To deploy a full version of the UI from a backend, run the following from the root fides directory:

```sh
    cd clients
    npm install
    cd admin-ui
    turbo run prod-export
```

This will build and place the Admin UI files into a location accessible by backend fides deployments.

To test the UI, run `nox -s dev` from the root directory, and visit `http://0.0.0.0:8080/index.html`.

## Privacy Center

To serve this application locally, first install your local dependencies by installing at the root `client` directory level:

In `/clients`:

```bash
npm install
```

Then, run:

```bash
cd privacy-center
turbo run dev
```

This will automatically build and run the project.

### Building

To build this application directly, run:

```bash
turbo run build
```

As a Next application, it will output build artifacts to the `.next` directory.

### Testing

To run the interactive test interface, run:

```bash
turbo run test
```

For a fully-loaded development & test setup of both the Privacy Center, run the following commands in two separate terminals:

```bash
cd privacy-center && turbo run dev
cd privacy-center && turbo run cy:open
```

There are two ways to test Fides consent components:

1. Navigate to `http://localhost:3000/fides-js-components-demo.html`. This page comes pre-packaged with some default configurations to get up and running quickly with the consent components, and is also the page used by cypress e2e tests. To test other configurations, edit the fidesConfig object passed into `Fides.init()` in `privacy-center/public/fides-js-components-demo.html`.
2. Navigate to `http://localhost:3000/fides-js-demo.html`. This page, unlike the above, calls the `/api/fides-js` Privacy Center endpoint. This endpoint loads config from the privacy center's legacy `config.json`, so it's closer to how a customer would actually use the `fides-js` package. In addition, we inject only the minimal config into `fides-js`. The overlay is not enabled by default on this page.
