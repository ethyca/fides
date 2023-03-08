import { stubPlus } from "cypress/support/stubs";

import { RoleRegistryEnum } from "~/types/api";

describe("Routes", () => {
  beforeEach(() => {
    cy.login();
  });

  // TODO: temporarily disabled due to https://github.com/ethyca/fides/issues/2769
  describe.skip("permissions", () => {
    beforeEach(() => {
      // For these tests, let's say we always have systems and connectors
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
      cy.intercept("GET", "/api/v1/connection*", {
        fixture: "connectors/list.json",
      }).as("getConnectors");
      stubPlus(true);
    });

    it("admins can access many routes", () => {
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.visit("/");
      cy.visit("/add-systems");
      cy.wait("@getSystems");
      cy.getByTestId("add-systems");
      cy.visit("/privacy-requests");
      cy.getByTestId("privacy-requests");
      cy.visit("/datastore-connection");
      cy.wait("@getConnectors");
      cy.getByTestId("connection-grid");
      cy.visit("/privacy-requests/configure");
      cy.getByTestId("privacy-requests-configure");
    });

    // This doesn't work right now due needing a fix for `exact` in the `nav-config` helpers
    // This is the same issue as https://github.com/ethyca/fides/issues/2731
    it.skip("contributors can not access configuration", () => {
      cy.assumeRole(RoleRegistryEnum.CONTRIBUTOR);
      cy.visit("/privacy-requests/configure");
      cy.getByTestId("home-content");
    });

    it("viewers and/or approvers can only access limited routes", () => {
      [
        RoleRegistryEnum.VIEWER,
        RoleRegistryEnum.APPROVER,
        RoleRegistryEnum.VIEWER_AND_APPROVER,
      ].forEach((role) => {
        cy.assumeRole(role);
        // cannot access /add-systems
        cy.visit("/add-systems");
        cy.getByTestId("add-systems").should("not.exist");
        cy.getByTestId("home-content");
        // cannot access /datastore-connection
        cy.visit("/datastore-connection");
        cy.getByTestId("connection-grid").should("not.exist");
        cy.getByTestId("home-content");
        // can access /privacy-requests
        cy.visit("/privacy-requests");
        cy.getByTestId("privacy-requests");
      });
    });
  });
});
