/// <reference types="cypress" />

Cypress.Commands.add("getByTestId", (selector, ...args) =>
  cy.get(`[data-testid='${selector}']`, ...args)
);

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
    }
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
