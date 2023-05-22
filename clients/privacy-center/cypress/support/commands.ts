/// <reference types="cypress" />
// eslint-disable-next-line import/no-extraneous-dependencies
import "cypress-wait-until";

import type { AppDispatch } from "~/app/store";
import type { FidesConfig } from "fides-js";

Cypress.Commands.add("getByTestId", (selector, ...args) =>
  cy.get(`[data-testid='${selector}']`, ...args)
);

Cypress.Commands.add("getRadio", (value = "true", ...args) =>
  cy.get(`input[type="radio"][value="${value}"]`, ...args)
);

Cypress.Commands.add("dispatch", (action) => {
  cy.window().its("store").invoke("dispatch", action);
});

Cypress.Commands.add("waitUntilCookieExists", (cookieName: string, ...args) => {
  cy.waitUntil(
    () =>
      cy
        .getCookie(cookieName)
        .then((cookie) => Boolean(cookie && cookie.value)),
    ...args
  );
});

Cypress.Commands.add("loadConfigFixture", (fixtureName: string, ...args) => {
  cy.getByTestId("logo");
  cy.fixture(fixtureName, ...args).then((config) => {
    cy.dispatch({ type: "config/loadConfig", payload: config }).then(
      () => config
    );
  });
});

Cypress.Commands.add("visitConsentDemo", (options?: FidesConfig) => {
  cy.visit("/fides-js-components-demo.html", {
    onBeforeLoad: (win) => {
      // eslint-disable-next-line no-param-reassign
      win.fidesConfig = options;
    },
  });
});

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to select DOM element by data-testid attribute
       * @example cy.getByTestId('clear-btn')
       */
      getByTestId(
        selector: string,
        options?: Partial<
          Cypress.Loggable &
            Cypress.Timeoutable &
            Cypress.Withinable &
            Cypress.Shadow
        >
      ): Chainable<JQuery<HTMLElement>>;
      /**
       * Custom command to select a radio input by its value. Value defaults to "true".
       * @example cy.getRadio().should("be.checked");
       */
      getRadio(
        value?: string,
        options?: Partial<
          Cypress.Loggable &
            Cypress.Timeoutable &
            Cypress.Withinable &
            Cypress.Shadow
        >
      ): Chainable<JQuery<HTMLElement>>;
      /**
       * Call `cy.dispatch(myAction())` to directly dispatch an action on the app's Redux store.
       * Note that this should only be used for functionality that is impossible (or very slow) to
       * implement using regular browser interactions, as this provides less end-to-end coverage.
       *
       * https://www.cypress.io/blog/2018/11/14/testing-redux-store/#dispatch-actions
       */
      dispatch(action: Parameters<AppDispatch>[0]): Chainable<any>;
      /**
       * Custom command to wait until a given cookie name exists. Sometimes this
       * is delayed, and Cypress' built-in default timeout is not used for
       * getCookie, surprisingly!
       * (see * https://github.com/cypress-io/cypress/issues/4802#issuecomment-941891554)
       *
       * @example cy.waitUntilCookieExists("fides_consent");
       */
      waitUntilCookieExists(
        cookieName: string,
        options?: Partial<
          Cypress.Loggable &
            Cypress.Timeoutable &
            Cypress.Withinable &
            Cypress.Shadow
        >
      ): Chainable<boolean>;
      /**
       * Custom command to load a Privacy Center configuration JSON file from a fixture.
       * Note that because it is injected into the Redux state, any subsequent page-load resets that with the original
       * config from the server-side.
       *
       * @example cy.loadConfigFixture("config/config_all.json").as("config");
       */
      loadConfigFixture(
        fixtureName: string,
        options?: Partial<Cypress.Timeoutable>
      ): Chainable<any>;
      /**
       * Visit the /fides-js-components-demo page and inject config options
       * @example cy.visitConsentDemo(fidesConfig);
       */
      visitConsentDemo(options?: FidesConfig): Chainable<any>;
    }
  }
}

// The fides-js-components-demo.html page is wired up to inject the
// `fidesConfig` into the Fides.init(...) function
declare global {
  interface Window {
    fidesConfig?: FidesConfig;
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
