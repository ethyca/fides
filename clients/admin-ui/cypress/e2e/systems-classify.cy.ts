import { stubHomePage, stubPlus } from "cypress/support/stubs";

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
      cy.getByTestId("data-flow-with-classification").contains(
        "has detected ingress systems"
      );
      cy.getByTestId("close-drawer-btn").click();

      // Only egresses exist
      cy.getByTestId("row-demo_marketing_system").click();
      cy.getByTestId("data-flow-with-classification").contains(
        "has detected egress systems"
      );
      cy.getByTestId("close-drawer-btn").click();

      // No classification exists
      cy.visit("/classify-systems"); // visit again to clear the redux cache
      cy.fixture("classify/system-details.json").then((details) => {
        cy.intercept("GET", "/api/v1/plus/classify/details/*", {
          body: { ...details, ingress: [], egress: [] },
        }).as("getClassifyDetailsEmpty");
      });
      cy.getByTestId("row-demo_marketing_system").click();
      cy.wait("@getClassifyDetailsEmpty");
      cy.getByTestId("no-classification");
    });
  });
});
