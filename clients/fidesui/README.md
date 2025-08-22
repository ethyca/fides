# Fides UI

This package is a result of migrating the [ethyca/fidesui](https://github.com/ethyca/fidesui) standalone repo into this monorepo. It includes components that are custom built for FidesUI. They may be built from scratch, or use a variety of Chakra components to create something new. Anything you would normally import from the Chakra library should be imported from `fidesui` instead, since this is all built on top of Chakra.

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

## How to use

This package is included in both the `admin-ui` and `privacy-center` NextJS applications as a turbo Internal Package called `fidesui` and will automatically get bundled in those projects by NextJS using `transpileModules`. This means that you can import components from this package directly in your NextJS application and there is no reason to prebuild these components. When making changes or creating new components here it's important to test them in the consuming applications to ensure that they work as expected.

## Storybook

The goal of this Storybook project is to keep an authoritative record of how to make design decisions and how to use our component library to implement them.
To get started, you can run `turbo run storybook` from the root of the `/clients` directory.
Docs on how to write stories can be found here: https://storybook.js.org/docs/writing-stories

#### Roadmap

- [x] Initial project setup
- [ ] Host on Chromatic or similar platform
- [ ] Implement Autodocs/MDX
- [ ] Migrate all existing design decisions from confluence and other sources
