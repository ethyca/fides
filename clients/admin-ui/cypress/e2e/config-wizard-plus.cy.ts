import { stubPlus } from "cypress/support/stubs";

import { System } from "~/types/api";

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
    cy.login();
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
      cy.intercept("POST", "/api/v1/system/upsert", []).as("upsertSystems");
    });

    it("Allows calling the runtime scanner with classify", () => {
      // Stub systems, but replace the fides keys so they match up with ones that
      // @getClassifyList would return
      cy.fixture("classify/list-systems.json").then((systemClassifications) => {
        cy.intercept("GET", "/api/v1/plus/classify*", systemClassifications).as(
          "getClassifyList"
        );
        const keys = systemClassifications.map((sc) => sc.dataset_key);
        cy.fixture("systems.json").then((systems: System[]) => {
          const alteredSystems = systems.map((s, idx) => {
            if (idx < keys.length) {
              return { ...s, fides_key: keys[idx], name: keys[idx] };
            }
            return s;
          });
          cy.intercept("GET", "/api/v1/system", alteredSystems).as(
            "getSystems"
          );
        });
      });

      goToRuntimeScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@getScanResults").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("classify=true");
      });
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
      cy.getByTestId("systems-classify-table");
      cy.url().should("contain", "classify-systems");
      cy.wait("@getClassifyList");

      // Check that the classified systems have a status
      cy.getByTestId("status-vzmgr-service").contains("Awaiting Review");
      cy.getByTestId("status-kube-dns").contains("Awaiting Review");
      cy.getByTestId("status-demo_marketing_system").contains("Unknown");
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
      cy.intercept("GET", "/api/v1/plus/scan*", {
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
