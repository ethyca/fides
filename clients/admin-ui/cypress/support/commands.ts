/// <reference types="cypress" />

import { STORAGE_ROOT_KEY } from "~/constants";
import { RoleRegistryEnum, ScopeRegistryEnum } from "~/types/api";

Cypress.Commands.add("getByTestId", (selector, options) =>
  cy.get(`[data-testid='${selector}']`, options),
);

Cypress.Commands.add("getByTestIdPrefix", (prefix, options) =>
  cy.get(`[data-testid^='${prefix}']`, options),
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
        }),
      );
    });
    cy.intercept("/api/v1/user/*/permission", {
      fixture: "user-management/permissions.json",
    }).as("getUserPermission");
  });
});

const getSelectOptionList = (selectorId: string) =>
  cy.getByTestId(selectorId).click().find(`.custom-select__menu-list`);

Cypress.Commands.add("selectOption", (selectorId, optionText) => {
  getSelectOptionList(selectorId).contains(optionText).click();
});

Cypress.Commands.add(
  "removeMultiValue",
  (selectorId: string, optionText: string) =>
    cy
      .getByTestId(selectorId)
      .contains(optionText)
      .siblings(".custom-select__multi-value__remove")
      .click(),
);

Cypress.Commands.add("clearSingleValue", (selectorId) =>
  cy.getByTestId(selectorId).find(".custom-select__clear-indicator").click(),
);

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

// this prevents an infinite loop that occurs sometimes and causes tests to
// fail-- see https://github.com/cypress-io/cypress/issues/20341
Cypress.on("uncaught:exception", (err) => {
  if (err.message.includes("ResizeObserver")) {
    // returning false here prevents Cypress from
    // failing the test
    return false;
  }
  return true;
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
      >,
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
      /**
       * @deprecated Selects an option from a CustomSelect component
       *
       * @example cy.getByTestId("input-allow_list_id").antSelect("Prime numbers")
       */
      selectOption(
        selectorId: string,
        optionText: string,
      ): Chainable<JQuery<HTMLElement>>;
      /**
       * Removes a value from a CustomSelect that is a multiselect
       *
       * @example removeMultiValue("input-multifield", "Eevee");
       */
      removeMultiValue(selectorId: string, optionText: string): void;
      /**
       * Clears the value of a CustomSelect that is a single select
       *
       * @example removeMultiValue("input-singlefield");
       */
      clearSingleValue(selectorId: string): void;
    }
  }
}

// Convert this to a module instead of script (allows import/export)
export {};
