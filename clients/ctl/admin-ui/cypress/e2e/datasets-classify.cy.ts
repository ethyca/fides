/**
 * This test suite is a parallel of datasets.cy.ts for testing Dataset features when the user has
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

    it("Classifies the dataset after generating it", () => {
      // Fill out the form.
      cy.visit("/dataset/new");
      cy.getByTestId("connect-db-btn").click();
      cy.getByTestId("input-url").type(
        "postgresql://postgres:fidesctl@fidesctl-db:5432/fidesctl_test"
      );
      cy.getByTestId("create-dataset-btn").click();

      // A modal opens to confirm the classify request.
      cy.getByTestId("confirmation-modal");

      // Confirmation will kick off the chain of API calls.
      cy.intercept("POST", "/api/v1/generate", {
        fixture: "generate/dataset.json",
      }).as("postGenerate");
      cy.intercept("POST", "/api/v1/dataset", { fixture: "dataset.json" }).as(
        "postDataset"
      );
      cy.intercept("POST", "/api/v1/plus/classification", {
        fixture: "classification/create.json",
      }).as("postClassification");
      cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
        "getDatasets"
      );

      // Confirm the request.
      cy.getByTestId("confirmation-modal").getByTestId("continue-btn").click();

      cy.wait("@postGenerate");
      cy.wait("@postDataset");
      cy.wait("@postClassification");
      cy.wait("@getDatasets");

      cy.url().should("match", /dataset$/);

      // The combination of Next routing and a toast message makes Cypress get weird
      // when re-running this test case. Introducing a delay fixes it.
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(100);
      cy.getByTestId("toast-success-msg");
    });
  });
});
