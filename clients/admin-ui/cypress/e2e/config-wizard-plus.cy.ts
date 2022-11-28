import { stubPlus } from "cypress/support/stubs";

/**
 * Handy function to bring us straight to the data flow scanner.
 * This could be put in a beforeEach, but then you can't overwrite intercepts
 */
const goToDataFlowScanner = () => {
  // Select Runtime scanner to move to scan step.
  cy.getByTestId("add-system-form");
  cy.getByTestId("data-flow-scan-btn").click();
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

  describe("Data flow scanner steps", () => {
    beforeEach(() => {
      // Stub scan endpoints
      cy.intercept("PUT", "/api/v1/plus/scan*", {
        delay: 500,
        fixture: "data-flow-scanner/list.json",
      }).as("putScanResults");
      cy.intercept("POST", "/api/v1/system/upsert", []).as("upsertSystems");
      cy.intercept("GET", "/api/v1/plus/scan/latest?diff=true", {
        statusCode: 404,
        body: { detail: "No saved system scans found." },
      }).as("getLatestScanDiff");
    });

    it("Allows calling the data flow scanner with classify", () => {
      cy.intercept("GET", "/api/v1/plus/classify?resource_type=systems*", {
        fixture: "data-flow-scanner/list-classify-systems.json",
      }).as("getClassifyList");

      goToDataFlowScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@putScanResults").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("classify=true");
      });
      cy.wait("@getLatestScanDiff");
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
      goToDataFlowScanner();
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

    it("Can rescan", () => {
      let numAddedSystems = 0;
      cy.fixture("data-flow-scanner/diff.json").then((diff) => {
        cy.intercept("GET", "/api/v1/plus/scan/latest?diff=true", {
          body: diff,
        }).as("getLatestScanDiff");
        numAddedSystems = diff.added_systems.length;
      });

      goToDataFlowScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@putScanResults");
      cy.wait("@getLatestScanDiff");
      cy.getByTestId("scan-results");

      // Should render just the added systems discovered from the diff
      cy.get("table")
        .find("tbody > tr")
        .then((rows) => {
          expect(rows.length).to.eql(numAddedSystems);
        });

      cy.getByTestId("register-btn").click();
      cy.wait("@upsertSystems");
      cy.getByTestId("systems-classify-table")
        .find("tbody > tr")
        .then((rows) => {
          expect(rows.length).to.eql(numAddedSystems);
        });
    });

    it("Renders an empty state", () => {
      // No newly added systems
      cy.fixture("data-flow-scanner/diff.json").then((diff) => {
        cy.intercept("GET", "/api/v1/plus/scan/latest?diff=true", {
          body: { ...diff, added_systems: [] },
        }).as("getLatestScanDiff");
      });
      goToDataFlowScanner();
      cy.getByTestId("scanner-loading");
      cy.wait("@putScanResults");
      cy.wait("@getLatestScanDiff");
      cy.getByTestId("scan-results");

      // No results message
      cy.getByTestId("no-results");
      cy.getByTestId("back-btn").click();
    });

    it("Can render an error", () => {
      cy.intercept("PUT", "/api/v1/plus/scan*", {
        statusCode: 404,
        body: {
          detail: "Item not found",
        },
      }).as("getScanError");
      goToDataFlowScanner();

      cy.wait("@getScanError");
      cy.getByTestId("scanner-error");
      cy.getByTestId("generic-msg");
      //   Canceling should bring us back to the add system form
      cy.getByTestId("cancel-btn").click();
      cy.getByTestId("add-system-form");
    });
  });
});
