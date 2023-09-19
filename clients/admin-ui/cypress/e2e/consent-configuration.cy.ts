import {
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { CONFIGURE_CONSENT_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("Consent configuration", () => {
  beforeEach(() => {
    cy.login();
  });

  describe("permissions", () => {
    it("cannot access consent config page without plus", () => {
      stubPlus(false);
      cy.visit(CONFIGURE_CONSENT_ROUTE);
      cy.getByTestId("home-content");
    });

    it("cannot access consent config page without privacy notice permission", () => {
      stubPlus(true);
      cy.assumeRole(RoleRegistryEnum.APPROVER);
      cy.visit(CONFIGURE_CONSENT_ROUTE);
      cy.getByTestId("home-content");
    });
  });

  describe("empty state", () => {
    it("can render an empty state", () => {
      stubPlus(true);
      cy.intercept("GET", "/api/v1/system", {
        body: [],
      }).as("getEmptySystems");
      cy.visit(CONFIGURE_CONSENT_ROUTE);
      cy.getByTestId("empty-state");
      cy.get("body").click(0, 0);
      cy.getByTestId("add-vendor-btn").click();
      cy.getByTestId("add-vendor-modal-content");
    });
  });

  describe("with existing systems", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      stubPlus(true);
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
      cy.visit(CONFIGURE_CONSENT_ROUTE);
    });

    it("can render existing systems and cookies", () => {
      // One row per system and one subrow per cookie
      cy.getByTestId("grouped-row-demo_analytics_system");
      cy.getByTestId("grouped-row-demo_marketing_system");
      cy.getByTestId("grouped-row-fidesctl_system");

      // One subrow per cookie. Should have corresponding data use
      cy.getByTestId("subrow-cell_0_Cookie name").contains("N/A");
      cy.getByTestId("subrow-cell_0_Data use").contains("N/A");
      cy.getByTestId("subrow-cell_1_Cookie name").contains("_ga");
      cy.getByTestId("subrow-cell_1_Data use").contains("advertising");
      cy.getByTestId("subrow-cell_2_Cookie name").contains("cookie");
      cy.getByTestId("subrow-cell_2_Data use").contains("Improve Service");
      cy.getByTestId("subrow-cell_3_Cookie name").contains("cookie2");
      cy.getByTestId("subrow-cell_3_Data use").contains("Improve Service");

      cy.getByTestId("add-cookie-btn");
      cy.getByTestId("add-vendor-btn");
    });
  });
});
