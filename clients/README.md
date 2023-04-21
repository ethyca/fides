# Clients

The clients directory houses all front-end packages and shared code amongst clients, and also includes e2e tests.

## Prerequisites

Dependencies within this directory are managed by Turborepo. Our root `package.json` file defines 3 workspaces (or packages) that are part of the Turbo ecosystem:
1. admin-ui
2. privacy-center
3. fides-consent

To run any or all workspaces, you'll have to complete the following setup: 

1. Install Turborepo globally so that you can use it on the command line `npm install turbo --global`
2. In `clients` folder, run `npm install`. This will install the dev dependency `turbo`. This will also install the appropriate dependencies in `clients` and in each client within `clients` folder. You may need to first remove all `node_modules` in each of the clients (admin-ui, privacy-center, etc)

## Running Locally

To run the project use `turbo` instead of `npm`. 

Incorrect:
```
npm run dev
```

Correct:
```
turbo run dev
```

Running this in the root `clients` folder will result in every workspace being run.

Running this command within `admin-ui` will result in only admin-ui being run.

Available commands that exist for every workspace are defined in the root `turbo.json` file, while commands unique to a specific workspace are defined in the `turbo.json` file within the workspace.

Each command maps to the npm command with the same name in the nearest `package.json`, moving up the working dir, ending at `clients/package.json`.

It's also important to use the turbo command because, as you see in the `turbo.json` files, we've defined some dependencies and caching details on some turbo commands. 



## Adding packages

To install packages in any package in `clients`, run the following from `clients`:
```
npm install <package> --workspace=<workspace>
```
Example:
```
npm install react --workspace=admin-ui
```
See https://turbo.build/repo/docs/handbook/package-installation#addingremovingupgrading-packages for more details