import { stubPlus } from "cypress/support/stubs";

/**
 * Handy function to bring us straight to the runtime scanner.
 * This could be put in a beforeEach, but then you can't overwrite intercepts
 */
const goToRuntimeScanner = () => {
  // Move past organization step.
  cy.getByTestId("organization-info-form");
  cy.getByTestId("submit-btn").click();

  // Select Runtime scanner to move to scan step.
  cy.getByTestId("add-system-form");
  cy.getByTestId("runtime-scan-btn").click();
};

/**
 * This test suite is a parallel of config-wizard.cy.ts for testing the config wizard flow
 * when the user has access to the Fides+.
 *
 * We skip these tests while the config wizard feature flag is set to false.
 */
describe.skip("Config wizard with plus settings", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organization.json",
    }).as("getOrganization");

    cy.intercept("PUT", "/api/v1/organization**", {
      fixture: "organization.json",
    }).as("updateOrganization");
  });

  beforeEach(() => {
    stubPlus(true);
    cy.visit("/config-wizard");
    cy.getByTestId("guided-setup-btn").click();
    cy.wait("@getOrganization");
  });

  describe("Runtime scanner steps", () => {
    beforeEach(() => {
      // Stub scan endpoints
      cy.intercept("GET", "/api/v1/plus/scan*", {
        delay: 500,
        fixture: "runtime-scanner/list.json",
      }).as("getScanResults");
    });

    it("Allows calling the runtime scanner", () => {
      goToRuntimeScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@getScanResults");
      cy.getByTestId("scan-results");
      //   TODO: make sure the systems show up in the table
    });

    it("Can render an error", () => {
      cy.intercept("GET", "/api/v1/plus/scan", {
        statusCode: 404,
        body: {
          detail: "Item not found",
        },
      }).as("getScanError");
      goToRuntimeScanner();

      cy.wait("@getScanError");
      cy.getByTestId("scanner-error");
      cy.getByTestId("generic-msg");
      //   Canceling should bring us back to the add system form
      cy.getByTestId("cancel-btn").click();
      cy.getByTestId("add-system-form");
    });
  });
});
