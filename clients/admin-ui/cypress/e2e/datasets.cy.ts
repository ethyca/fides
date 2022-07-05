describe("Dataset", () => {
  describe("List of datasets view", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" });
    });
    it("Can navigate to the datasets list view", () => {
      cy.visit("/");
      cy.getByTestId("nav-link-Datasets").click();
      cy.getByTestId("dataset-table");
      cy.getByTestId("dataset-row-demo_users_dataset_4");
    });
  });
});
