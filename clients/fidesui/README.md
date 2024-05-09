# Fides UI

This package is a result of migrating the [ethyca/fidesui](https://github.com/ethyca/fidesui) standalone repo into this monorepo. It includes components that are custom built for FidesUI. They may be built from scratch, or use a variety of Chakra components to create something new.

## Migration notes

A few of the main differences between the standalone and this are:

- This is now part of the turbo monorepo when imported as an [Internal Package](https://github.com/vercel/turbo/blob/v1.9.3/docs/pages/repo/docs/handbook/sharing-code/internal-packages.mdx)
- Fides UI now gets bundled by NextJS using the [next-transpile-modules](https://www.npmjs.com/package/next-transpile-modules) npm package
- For now does not have a Storybook implementation as we investigate and determine the future of this project.
- In light of all of the above, Lerna is no longer needed or included.

## What should go in here

In general, components that need to be shared across Fides applications should go in here in order to ensure a consistent UI. This may involve needing to import types specific to the Fides API as needed.

Some things that may not belong in this repo ([original discussion](https://github.com/ethyca/fidesui/pull/27#discussion_r1010820430)):

- Routing/pages. (Maybe helpers, but not the definitions of specific routes.)
- Mutation types. These usually involve a sequence calls that require UI-specific handling. (Maybe basic CRUD could be shared, at most).
