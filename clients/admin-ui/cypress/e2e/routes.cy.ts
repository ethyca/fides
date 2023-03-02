import { stubPlus } from "cypress/support/stubs";

import { RoleRegistry } from "~/types/api";

describe("Routes", () => {
  beforeEach(() => {
    cy.login();
  });

  describe("permissions", () => {
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
      cy.assumeRole(RoleRegistry.ADMIN);
      cy.visit("/");
      cy.visit("/add-systems");
      cy.wait("@getSystems");
      cy.getByTestId("add-systems");
      cy.visit("/privacy-requests");
      cy.getByTestId("privacy-requests");
      cy.visit("/datastore-connection");
      cy.wait("@getConnectors");
      cy.getByTestId("connection-grid");
    });

    it("viewers and/or approvers can only access limited routes", () => {
      [
        RoleRegistry.VIEWER,
        RoleRegistry.PRIVACY_REQUEST_MANAGER,
        RoleRegistry.VIEWER_AND_PRIVACY_REQUEST_MANAGER,
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
