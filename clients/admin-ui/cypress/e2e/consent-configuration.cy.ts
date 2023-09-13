import { stubPlus, stubSystemCrud } from "cypress/support/stubs";

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
      stubPlus(true);
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
      cy.visit(CONFIGURE_CONSENT_ROUTE);
    });

    it("can render existing systems and cookies", () => {
      // TODO: flesh out this test once we have our table
      cy.getByTestId("configure-consent-page").contains(
        "Demo Analytics System"
      );
      cy.getByTestId("add-cookie-btn");
      cy.getByTestId("add-vendor-btn");
    });
  });
});
