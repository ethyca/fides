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
import "cypress-file-upload";

import { stubHomePage, stubPlus, stubSystemCrud } from "./stubs";

// Disable CSS animations/transitions for all tests. The Chromium
// --force-prefers-reduced-motion flag handles this in Chrome, but Electron
// (the default CI browser) ignores it, causing antd animation race conditions.
// This fires on every page load (including cy.visit), before React renders.
Cypress.on("window:before:load", (win) => {
  // Stub matchMedia so FidesUIProvider detects prefers-reduced-motion and
  // sets antd's motion: false token before the first render.
  const original = win.matchMedia.bind(win);
  win.matchMedia = (query: string) => {
    if (query === "(prefers-reduced-motion: reduce)") {
      return {
        matches: true,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      } as MediaQueryList;
    }
    return original(query);
  };

  // Belt-and-suspenders: also inject CSS to kill any animations that aren't
  // controlled by antd's motion token (e.g. raw CSS transitions on drawers).
  const style = win.document.createElement("style");
  style.textContent = `
    *, *::before, *::after {
      transition-duration: 0s !important;
      transition-delay: 0s !important;
      animation-duration: 0s !important;
      animation-delay: 0s !important;
    }
  `;
  win.document.documentElement.appendChild(style);
});

// Stub global subscriptions because they are required for every page. These just default
// responses -- interceptions defined later will override them.
beforeEach(() => {
  cy.intercept("/api/v1/**", (req) => {
    console.warn(`⚠️ Unstubbed API request detected: ${req.method} ${req.url}`);
    req.reply({ statusCode: 404 });
  }).as("unstubbedRequest"); // default stub for all requests
  stubHomePage();
  stubSystemCrud();
  stubPlus(false);
});

// Alternatively you can use CommonJS syntax:
// require('./commands')
