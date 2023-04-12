/// <reference types="cypress" />

import { STORAGE_ROOT_KEY } from "~/constants";
import { RoleRegistryEnum, ScopeRegistryEnum } from "~/types/api";

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
      fixture: "user-management/permissions.json",
    }).as("getUserPermission");
  });
});

Cypress.Commands.add("assumeRole", (role) => {
  cy.fixture("scopes/roles-to-scopes.json").then((mapping) => {
    const scopes: ScopeRegistryEnum[] = mapping[role];
    cy.fixture("login.json").then((body) => {
      const { id: userId } = body.user_data;
      cy.intercept(`/api/v1/user/${userId}/permission`, {
        body: {
          id: userId,
          user_id: userId,
          roles: [role],
          total_scopes: scopes,
        },
      }).as("getUserPermission");
    });
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
       * @example cy.assumeRole(RoleRegistryEnum.OWNER)
       */
      assumeRole(role: RoleRegistryEnum): void;
    }
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
