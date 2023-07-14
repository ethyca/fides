# Clients

The clients directory houses all front-end packages and shared code amongst clients, and also includes e2e tests.

## Prerequisites

To run and develop the Fides UI components locally, you'll need to do the following:

1. Clone the [Fides repository](https://github.com/ethyca/fides/)
2. Install [Node.js](https://nodejs.org/en/download/)
3. Globally install [Turbo](https://turbo.build/repo/docs/installing)
4. In the `clients` folder, run `npm install`. This will install the dev dependency `turbo`. This will also install the appropriate dependencies in `clients` and in each client within `clients` folder. You may need to first remove all `node_modules` in each of the clients (admin-ui, privacy-center, etc)

Dependencies within this directory are managed by Turborepo. Our root `package.json` file defines 3 workspaces (or packages) that are part of the Turbo ecosystem:

1. admin-ui
2. privacy-center
3. fides-js

## Running Locally

Correct:

```sh
turbo run dev
```

Running this in the root `clients` folder will result in every workspace being run.

Running this command within `admin-ui` will result in only admin-ui being run.

Available commands that exist for every workspace are defined in the root `turbo.json` file, while commands unique to a specific workspace are defined in the `turbo.json` file within the workspace.

It's important to use the turbo command because, as you see in the `turbo.json` files, we've defined some dependencies and caching details on some turbo commands.

## Adding packages

To install packages in any package in `clients`, run the following from `clients`:

```sh
npm install <package> --workspace=<workspace>
```

Example:

```sh
npm install react --workspace=admin-ui
```

See https://turbo.build/repo/docs/handbook/package-installation#addingremovingupgrading-packages for more details
