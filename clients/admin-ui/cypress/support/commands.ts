/// <reference types="cypress" />

import { STORAGE_ROOT_KEY } from "~/constants";

Cypress.Commands.add("getByTestId", (selector, ...args) =>
  cy.get(`[data-testid='${selector}']`, ...args)
);

Cypress.Commands.add("login", () => {
  cy.fixture("login.json").then((body) => {
    const authState = {
      user_data: body.user_data,
      token: body.token_data.access_token,
    };
    window.localStorage.setItem(
        STORAGE_ROOT_KEY,
      JSON.stringify(authState)
    );
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
       * Programmatically login with a mock user
       */
      login(): void;
    }
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
