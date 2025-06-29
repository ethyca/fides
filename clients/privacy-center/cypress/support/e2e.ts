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

import { stubIdVerification } from "./stubs";

beforeEach(() => {
  cy.intercept("/api/v1/**", (req) => {
    // eslint-disable-next-line no-console
    console.warn(`⚠️ Unstubbed API request detected: ${req.method} ${req.url}`);
    req.reply({ statusCode: 404 });
  }).as("unstubbedRequest"); // default stub for all requests
  // All of these tests assume identity verification is required.
  stubIdVerification();
});
