/// <reference types="cypress" />

import { STORAGE_ROOT_KEY, USER_PRIVILEGES } from "~/constants";

Cypress.Commands.add("getByTestId", (selector, ...args) =>
  cy.get(`[data-testid='${selector}']`, ...args)
);

Cypress.Commands.add("login", () => {
  cy.fixture("login.json").then((body) => {
    const authState = {
      user: body.user_data,
      token: body.token_data.access_token,
    };
    cy.window().then((win) => {
      win.localStorage.setItem(
        STORAGE_ROOT_KEY,
        // redux-persist stringifies the root object _and_ the first layer of children.
        // https://github.com/rt2zz/redux-persist/issues/489#issuecomment-336928988
        JSON.stringify({
          auth: JSON.stringify(authState),
        })
      );
    });
    cy.intercept("/api/v1/user/*/permission", {
      body: {
        id: body.user_data.id,
        user_id: body.user_data.id,
        scopes: USER_PRIVILEGES.map((up) => up.scope),
      },
    }).as("getUserPermission");
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
