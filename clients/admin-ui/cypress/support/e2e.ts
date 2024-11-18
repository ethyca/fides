// ***********************************************************
// This example support/e2e.ts is processed and
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
import "./ant-support";
// eslint-disable-next-line import/no-extraneous-dependencies
import "cypress-real-events";

import { stubHomePage, stubPlus, stubSystemCrud } from "./stubs";

// Stub global subscriptions because they are required for every page. These just default
// responses -- interceptions defined later will override them.
beforeEach(() => {
  stubHomePage();
  stubSystemCrud();
  stubPlus(false);
});

// Alternatively you can use CommonJS syntax:
// require('./commands')
