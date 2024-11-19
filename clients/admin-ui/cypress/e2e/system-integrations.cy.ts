import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";

describe("System integrations", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(false);
    stubSystemIntegrations();
    stubSystemCrud();
    stubDatasetCrud();
    stubTaxonomyEntities();
    cy.visit(SYSTEM_ROUTE);
  });

  it("should render the integration configuration panel when navigating to integrations tab", () => {
    cy.getByTestId("system-fidesctl_system").within(() => {
      cy.getByTestId("edit-btn").click();
    });
    cy.getByTestId("tab-Integrations").click();
    cy.getByTestId("tab-panel-Integrations").should("exist");
  });

  describe("Integration search", () => {
    beforeEach(() => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("tab-Integrations").click();
      cy.getByTestId("select-dropdown-btn").click();
    });

    it("should display Shopify when searching with upper case letters", () => {
      cy.getByTestId("input-search-integrations").type("Sho");
      cy.getByTestId("select-dropdown-list")
        .find('[role="menuitem"] p')
        .should("contain.text", "Shopify");
    });

    it("should display Shopify when searching with lower case letters", () => {
      cy.getByTestId("input-search-integrations").type("sho");
      cy.getByTestId("select-dropdown-list")
        .find('[role="menuitem"] p')
        .should("contain.text", "Shopify");
    });
  });

  describe("Integration form contents", () => {
    beforeEach(() => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("tab-Integrations").click();
      cy.getByTestId("select-dropdown-btn").click();

      cy.getByTestId("input-search-integrations").type("PostgreSQL");
      cy.getByTestId("select-dropdown-list")
        .contains('[role="menuitem"]', "PostgreSQL")
        .click();
    });

    it("should not Request types (enabled-actions) field", () => {
      cy.getByTestId("enabled-actions").should("not.exist");
    });
  });
});
