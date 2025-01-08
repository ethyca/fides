import {
  stubDatamap,
  stubPlus,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

describe("Datamap table and spatial view", () => {
  beforeEach(() => {
    cy.login();
    stubDatamap();
    stubTaxonomyEntities();
    stubPlus(true);
  });

  it("Can render spatial view", () => {
    cy.visit("/datamap");
    cy.wait("@getDatamap");
    cy.getByTestId("cytoscape-graph").should("exist");
  });

  it("Renders a modal to prompt the user to get started when there is no datamap yet", () => {
    // Button only shows up when data map is empty (no systems)
    cy.intercept("GET", "/api/v1/plus/datamap/*", {
      fixture: "datamap/empty_datamap.json",
    }).as("getEmptyDatamap");
    cy.visit("/datamap");
    cy.wait("@getEmptyDatamap");

    cy.getByTestId("get-started-modal");
    cy.getByTestId("add-systems-btn").click();
    cy.url().should("contain", "/add-systems");
  });
});
