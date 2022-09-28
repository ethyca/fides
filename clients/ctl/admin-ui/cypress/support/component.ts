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
import "@fontsource/inter/700.css";

import { ChakraProvider } from "@chakra-ui/react";
// Alternatively you can use CommonJS syntax:
// require('./commands')
// eslint-disable-next-line import/no-extraneous-dependencies
import { mount } from "cypress/react";
import * as React from "react";

import theme from "../../src/theme";

// Augment the Cypress namespace to include type definitions for
// your custom command.
// Alternatively, can be defined in cypress/support/component.d.ts
// with a <reference path="./component" /> at the top of your spec.
declare global {
  namespace Cypress {
    interface Chainable {
      mount: typeof mount;
    }
  }
}

Cypress.Commands.add("mount", (jsx, options) =>
  mount(React.createElement(ChakraProvider, { theme }, jsx), options)
);

// Example use:
// cy.mount(<MyComponent />)
