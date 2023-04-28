/// <reference types="cypress" />
// eslint-disable-next-line import/no-extraneous-dependencies
import "cypress-wait-until";

import type { AppDispatch } from "~/app/store";

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
  cy.waitUntil(() => cy.getCookie(cookieName).then(cookie => Boolean(cookie && cookie.value)), ...args);
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
       *
       * TODO(ssangervasi): Make the action object less permissive. Right now it can be `AnyAction`
       * by inferring it this way, which means we don't get good intellisense when writing tests.
       * Unfortunately we also can't use action creators (such as
       * `configSlice.actions.overrideConsentOptions(payload)`) because that would require importing
       * the whole RTK store, which Cypress can't/shouldn't do.
       */
      dispatch: (action: Parameters<AppDispatch>[0]) => void;
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
      ): Chainable<JQuery<HTMLElement>>;
    }
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
