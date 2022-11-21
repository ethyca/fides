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
 */
describe("Config wizard with plus settings", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organization.json",
    }).as("getOrganization");

    cy.intercept("PUT", "/api/v1/organization**", {
      fixture: "organization.json",
    }).as("updateOrganization");
    stubPlus(true);

    // Go through the initial config wizard steps
    cy.visit("/add-systems");
    cy.getByTestId("guided-setup-btn").click();
    cy.wait("@getOrganization");
  });

  describe("Runtime scanner steps", () => {
    beforeEach(() => {
      // Stub scan endpoints
      cy.intercept("PUT", "/api/v1/plus/scan*", {
        delay: 500,
        fixture: "runtime-scanner/list.json",
      }).as("putScanResults");
      cy.intercept("POST", "/api/v1/system/upsert", []).as("upsertSystems");
    });

    it("Allows calling the runtime scanner with classify", () => {
      cy.intercept("GET", "/api/v1/plus/classify?resource_type=systems*", {
        fixture: "classify/list-systems.json",
      }).as("getClassifyList");

      goToRuntimeScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@putScanResults").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("classify=true");
      });
      cy.getByTestId("scan-results");

      // Check that the systems we expect are in the results table
      const numSystems = 42;
      cy.getByTestId("checkbox-fidesctl-demo");
      cy.getByTestId("checkbox-postgres");
      cy.get("table")
        .find("tbody > tr")
        .then((rows) => {
          expect(rows.length).to.eql(numSystems);
        });
      cy.getByTestId("register-btn").click();
      cy.wait("@upsertSystems").then((interception) => {
        const { body } = interception.request;
        expect(body.length).to.eql(numSystems);
      });
      cy.getByTestId("systems-classify-table");
      cy.url().should("contain", "classify-systems");

      cy.wait("@getClassifyList").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("vzmgr-service");
        expect(url).to.contain("kube-dns");
      });

      // Check that the classified systems have a status
      cy.getByTestId("status-vzmgr-service").contains("Awaiting Review");
      cy.getByTestId("status-kube-dns").contains("Awaiting Review");
      cy.getByTestId("status-pl-elastic-es-transport").contains("Unknown");
    });

    it("Can register a subset of systems", () => {
      cy.intercept("GET", "/api/v1/plus/classify?resource_type=systems*", {
        fixture: "classify/list-systems.json",
      }).as("getClassifyList");
      goToRuntimeScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@putScanResults");
      cy.getByTestId("scan-results");

      // Uncheck all of the systems by clicking the select all box
      cy.get("th").first().click();
      cy.getByTestId("register-btn").should("be.disabled");
      // Check just two systems
      const systems = ["vzmgr-service", "kube-dns"];
      systems.forEach((s) => {
        cy.getByTestId(`checkbox-${s}`).click();
      });
      cy.getByTestId("register-btn").click();
      cy.getByTestId("warning-modal-confirm-btn").click();
      cy.wait("@upsertSystems").then((interception) => {
        const { body } = interception.request;
        expect(body.map((s) => s.fides_key)).to.eql(systems);
      });

      // Make sure there are only two systems in this table
      cy.getByTestId("systems-classify-table");
      cy.getByTestId("status-vzmgr-service");
      cy.getByTestId("status-kube-dns");
      cy.get("table")
        .find("tbody > tr")
        .then((rows) => {
          expect(rows.length).to.eql(2);
        });
    });

    it("Can render an error", () => {
      cy.intercept("PUT", "/api/v1/plus/scan*", {
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
