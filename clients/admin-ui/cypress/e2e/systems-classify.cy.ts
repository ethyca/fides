import { stubHomePage, stubPlus } from "cypress/support/stubs";

describe("Classify systems page", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/system", { fixture: "systems.json" }).as(
      "getSystems"
    );
  });

  it("Should reroute if not in plus", () => {
    stubHomePage();
    cy.visit("/classify-systems");
    cy.url().should("eql", `${Cypress.config().baseUrl}/`);
  });

  describe("With plus enabled", () => {
    beforeEach(() => {
      stubPlus(true);
      cy.intercept("GET", "/api/v1/plus/classify*", {
        fixture: "classify/list-systems.json",
      }).as("getClassifyList");
    });

    it("Should be accessible to plus users", () => {
      cy.visit("/classify-systems");
      cy.getByTestId("systems-classify-table");
    });
  });
});
