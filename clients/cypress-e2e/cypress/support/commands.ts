/// <reference types="cypress" />
import { CREDENTIALS } from "./constants";

Cypress.Commands.add("getByTestId", (selector, ...args) =>
  cy.get(`[data-testid='${selector}']`, ...args),
);

Cypress.Commands.add("getToggle", (...args) =>
  cy.get(`input[type="checkbox"]`, ...args),
);

Cypress.Commands.add("login", () => {
  cy.getByTestId("input-username").type(CREDENTIALS.username);
  cy.getByTestId("input-password").type(CREDENTIALS.password);
  cy.getByTestId("sign-in-btn").click();
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
        >,
      ): Chainable<JQuery<HTMLElement>>;
      /**
       * Custom command to select a checkbox input by its value.
       * @example cy.getToggle().should("be.checked");
       */
      getToggle(
        options?: Partial<
          Cypress.Loggable &
            Cypress.Timeoutable &
            Cypress.Withinable &
            Cypress.Shadow
        >,
      ): Chainable<JQuery<HTMLElement>>;
      /**
       * Log in. Must navigate to the login page before this command.
       */
      login(): void;
    }
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
