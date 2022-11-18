import {
  stubHomePage,
  stubPlus,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { System } from "~/types/api";

describe("Classify systems page", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/system", { fixture: "systems.json" }).as(
      "getSystems"
    );
  });

  it("Should reroute if not in plus", () => {
    stubHomePage();
    stubPlus(false);
    cy.visit("/classify-systems");
    cy.url().should("eql", `${Cypress.config().baseUrl}/`);
  });

  describe("With plus enabled", () => {
    beforeEach(() => {
      stubPlus(true);
      stubTaxonomyEntities();
      // Stub both GET systems and GET classifications such that they will have overlap
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
    });

    it("Should be accessible to plus users", () => {
      cy.visit("/classify-systems");
      cy.getByTestId("systems-classify-table");
    });

    it("Should render an empty state if no classifications are found", () => {
      cy.intercept("GET", "/api/v1/plus/classify*", {
        body: [],
      }).as("getEmptyClassifyList");
      cy.visit("/classify-systems");
      cy.getByTestId("no-classifications");
    });

    it("Should render a proper description based on the existence of classification and data flows", () => {
      cy.intercept("GET", "/api/v1/plus/classify/details/*", {
        fixture: "classify/system-details.json",
      });
      cy.visit("/classify-systems");

      // No data flows exist on the system
      cy.getByTestId("row-vzmgr-service").click();
      cy.getByTestId("no-data-flows");
      cy.getByTestId("close-drawer-btn").click();

      // Only ingresses exist
      cy.getByTestId("row-kube-dns").click();
      cy.getByTestId("data-flow-with-classification").contains("receives data");
      cy.getByTestId("close-drawer-btn").click();

      // Only egresses exist
      cy.getByTestId("row-demo_marketing_system").click();
      cy.getByTestId("data-flow-with-classification").contains("sends data");
      cy.getByTestId("close-drawer-btn").click();

      // No classifications determined, though classify did run
      cy.visit("/classify-systems"); // visit again to clear the redux cache
      cy.fixture("classify/system-details.json").then((details) => {
        cy.intercept("GET", "/api/v1/plus/classify/details/*", {
          body: { ...details, ingress: [], egress: [] },
        }).as("getClassifyDetailsEmpty");
      });
      cy.getByTestId("row-demo_marketing_system").click();
      cy.wait("@getClassifyDetailsEmpty");
      cy.getByTestId("no-classification");

      // Classification is still in progress
      cy.visit("/classify-systems");
      cy.fixture("classify/system-details.json").then((details) => {
        cy.intercept("GET", "/api/v1/plus/classify/details/*", {
          body: { ...details, ingress: [], egress: [], status: "Processing" },
        }).as("getClassifyDetailsProcessing");
      });
      cy.getByTestId("row-demo_marketing_system").click();
      cy.getByTestId("processing");

      // No classification ever occurred
      cy.visit("/classify-systems");
      cy.intercept("GET", "/api/v1/plus/classify/details/*", {
        body: {},
      }).as("getClassifyEmpty");
      cy.getByTestId("row-demo_marketing_system").click();
      cy.getByTestId("no-classification-instance");
      cy.getByTestId("classification-status-badge").contains("Unknown");
    });

    it("Can edit a system's data flows", () => {
      cy.intercept("GET", "/api/v1/plus/classify/details/*", {
        fixture: "classify/system-details.json",
      });
      cy.intercept("PUT", "/api/v1/plus/classify/*", { body: undefined }).as(
        "putClassifyInstance"
      );
      cy.intercept("PUT", "/api/v1/system*", { fixture: "system.json" }).as(
        "putSystem"
      );
      cy.visit("/classify-systems");

      // Open up an ingress
      cy.getByTestId("row-kube-dns").click();
      cy.getByTestId("accordion-item-ingress").click();
      cy.getByTestId("accordion-item-demo_marketing_system").click();
      // Should have the classified suggestion
      cy.getByTestId("classified-select").contains("system");
      // Select a category from the taxonomy.
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("data-category-checkbox-tree")
        .contains("User Data")
        .click();
      cy.getByTestId("data-category-done-btn").click();
      cy.getByTestId("classified-select").contains("user");

      // Trigger a save
      cy.getByTestId("save-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.ingress[0].data_categories).to.eql(["system", "user"]);
      });
      cy.wait("@putClassifyInstance").then((interception) => {
        const { body } = interception.request;
        expect(body).to.eql({
          dataset_fides_key: "kube-dns",
          status: "Reviewed",
        });
      });
      cy.getByTestId("toast-success-msg");
    });
  });
});
