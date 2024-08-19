// ***********************************************************
// This example support/component.ts is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import "./commands";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";

import { EnhancedStore } from "@reduxjs/toolkit";
// Alternatively you can use CommonJS syntax:
// require('./commands')
// eslint-disable-next-line import/no-extraneous-dependencies
import { mount, MountOptions, MountReturn } from "cypress/react";
import { FidesUIProvider } from "fidesui";
import * as React from "react";
import { Provider } from "react-redux";

import { makeStore, RootState } from "~/app/store";
import theme from "~/theme";

// Augment the Cypress namespace to include type definitions for
// your custom command.
// Alternatively, can be defined in cypress/support/component.d.ts
// with a <reference path="./component" /> at the top of your spec.
declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Mounts a React node
       * @param component React Node to mount
       * @param options Additional options to pass into mount
       */
      mount(
        component: React.ReactNode,
        options?: MountOptions & { reduxStore?: EnhancedStore<RootState> },
      ): Cypress.Chainable<MountReturn>;
    }
  }
}

/**
 * Wrap the default mount in Redux and Chakra
 */
Cypress.Commands.add("mount", (component, options = {}) => {
  const { reduxStore = makeStore(), ...mountOptions } = options;
  const wrapChakra = React.createElement(FidesUIProvider, { theme }, component);
  const wrapRedux = React.createElement(
    Provider,
    { store: reduxStore },
    wrapChakra,
  );
  return mount(wrapRedux, mountOptions);
});
