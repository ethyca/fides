import { stubDatamap, stubPlus } from "cypress/support/stubs";

describe("Datamap table and spatial view", () => {
  beforeEach(() => {
    cy.login();
    stubDatamap();
    stubPlus(true);
  });

  it("Can render only render one view at a time", () => {
    cy.visit("/datamap");
    cy.wait("@getDatamap");

    // Only the spatial view should be visible first
    cy.getByTestId("cytoscape-graph");
    cy.getByTestId("datamap-table").should("not.exist");

    // Now table view
    cy.getByTestId("table-btn").click();
    cy.getByTestId("datamap-table");
    cy.getByTestId("cytoscape-graph").should("not.exist");

    // Now only the spatial view
    cy.getByTestId("map-btn").click();
    cy.getByTestId("cytoscape-graph");
    cy.getByTestId("datamap-table").should("not.exist");

    // Now table view
    cy.getByTestId("table-btn").click();
    cy.getByTestId("datamap-table");
    cy.getByTestId("cytoscape-graph").should("not.exist");

    // Clicking on the table view again should keep the table view open
    cy.getByTestId("table-btn").click();
    cy.getByTestId("datamap-table");
    cy.getByTestId("cytoscape-graph").should("not.exist");
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
