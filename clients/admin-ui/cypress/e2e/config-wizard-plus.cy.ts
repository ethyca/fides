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
      cy.intercept({
        method: "POST",
        url: "/api/v1/system/upsert",
      }).as("upsertSystems");
    });

    it("Allows calling the runtime scanner", () => {
      goToRuntimeScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@getScanResults");
      cy.getByTestId("scan-results");

      // Check that the systems we expect are in the results table
      const numSystems = 42;
      cy.getByTestId("checkbox-fidesctl-demo");
      cy.getByTestId("checkbox-postgres");
      cy.get("table")
        .find("tr")
        .then((rows) => {
          expect(rows.length).to.eql(numSystems + 1); // +1 for the header row
        });
      cy.getByTestId("register-btn").click();
      cy.wait("@upsertSystems").then((interception) => {
        const { body } = interception.request;
        expect(body.length).to.eql(numSystems);
      });
      /* This will redirect to localhost:3000/datamap instead of localhost:4000/datamap
       * which is not actually what we want.
       * However, it is difficult to test across zones, so all we can do is assert the path is right
       */
      cy.url().should("contain", "datamap");
    });

    it("Can register a subset of systems", () => {
      goToRuntimeScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@getScanResults");
      cy.getByTestId("scan-results");

      // Uncheck all of the systems by clicking the select all box
      cy.get("th").first().click();
      cy.getByTestId("register-btn").should("be.disabled");
      // Check just two systems
      const systems = ["fidesctl-demo", "postgres"];
      systems.forEach((s) => {
        cy.getByTestId(`checkbox-${s}`).click();
      });
      cy.getByTestId("register-btn").click();
      cy.getByTestId("warning-modal-confirm-btn").click();
      cy.wait("@upsertSystems").then((interception) => {
        const { body } = interception.request;
        expect(body.map((s) => s.fides_key)).to.eql(systems);
      });
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
