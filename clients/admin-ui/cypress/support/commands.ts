/// <reference types="cypress" />

import { STORAGE_ROOT_KEY, USER_PRIVILEGES } from "~/constants";
import { RoleRegistry, ScopeRegistry } from "~/types/api";

Cypress.Commands.add("getByTestId", (selector, options) =>
  cy.get(`[data-testid='${selector}']`, options)
);

Cypress.Commands.add("getByTestIdPrefix", (prefix, options) =>
  cy.get(`[data-testid^='${prefix}']`, options)
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

Cypress.Commands.add("assumeRole", (role) => {
  cy.fixture("scopes/roles-to-scopes.json").then((mapping) => {
    const scopes: ScopeRegistry[] = mapping[role];
    cy.intercept("/api/v1/user/*/permission", {
      body: {
        id: 123,
        user_id: 123,
        scopes,
      },
    }).as("getUserPermission");
  });
});

declare global {
  namespace Cypress {
    type GetBy = (
      selector: string,
      options?: Partial<
        Cypress.Loggable &
          Cypress.Timeoutable &
          Cypress.Withinable &
          Cypress.Shadow
      >
    ) => Chainable<JQuery<HTMLElement>>;

    interface Chainable {
      /**
       * Custom command to select DOM element by data-testid attribute.
       * @example cy.getByTestId('clear-btn')
       */
      getByTestId: GetBy;
      /**
       * Custom command to select DOM element by the prefix of a data-testid attribute. Useful for
       * elements that get rendered in a list where each item has its own unique id.
       *
       * @example
       * cy.getByTestIdPrefix('row')
       * // => [ tr#01, tr#02, ..., tr#20]
       * // Versus:
       * cy.getByTestId('row-13')
       * // => tr#13
       */
      getByTestIdPrefix: GetBy;
      /**
       * Programmatically login with a mock user
       */
      login(): void;
      /**
       * Stub a user with the scopes associated with a role
       * @example cy.assumeRole(RoleRegistry.ADMIN)
       */
      assumeRole(role: RoleRegistry): void;
    }
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
