/**
 * This test suite is a parallel of datests.cy.ts for testing Dataset features when the user has
 * access to the  Fidescls API. This suite should cover the behavior that is different when a
 * dataset is classified.
 */
describe("Datasets with Fides Classify", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/plus/health", {
      statusCode: 200,
      body: {
        status: "healthy",
        core_fidesctl_version: "1.8",
      },
    }).as("getPlusHealth");
  });

  describe("Creating datasets", () => {
    it("Shows the classify switch", () => {
      cy.visit("/dataset/new");
      cy.getByTestId("connect-db-btn").click();

      cy.getByTestId("input-classify").find("input").should("be.checked");
      cy.getByTestId("input-classify").click();
      cy.getByTestId("input-classify").find("input").should("not.be.checked");
    });
  });
});
