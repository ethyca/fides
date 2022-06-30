describe("Dataset", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" });
    cy.intercept("GET", "/api/v1/dataset/*", { fixture: "dataset.json" });
    cy.intercept("GET", "/api/v1/data_category", {
      fixture: "data_category.json",
    });
  });

  describe("List of datasets view", () => {
    it("Can navigate to the datasets list view", () => {
      cy.visit("/");
      cy.getByTestId("nav-link-Datasets").click();
      cy.getByTestId("dataset-table");
      cy.getByTestId("dataset-row-demo_users_dataset_4");
      cy.url().should("contain", "/dataset");
    });

    it("Can navigate to the datasets view via URL", () => {
      cy.visit("/dataset");
      cy.getByTestId("dataset-table");
    });

    it("Can load an individual dataset", () => {
      cy.visit("/dataset");
      cy.getByTestId("load-dataset-btn").should("be.disabled");
      cy.getByTestId("dataset-row-demo_users_dataset").click();
      cy.getByTestId("load-dataset-btn").should("not.be.disabled");
      cy.getByTestId("load-dataset-btn").click();
      cy.getByTestId("dataset-fields-table");
      cy.url().should("contain", "/dataset/demo_users_dataset");
    });
  });

  describe("Dataset fields view", () => {
    it("Can navigate to edit a dataset via URL", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("dataset-fields-table");
    });

    it("Can render an edit form for a dataset field with existing values", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("edit-drawer-content");
      cy.getByTestId("description-input").should(
        "have.value",
        "User's unique ID"
      );
      cy.getByTestId("identifiability-input").should("contain", "Identified");
      cy.getByTestId("selected-categories").children().should("have.length", 1);
      // cypress has trouble with testid's that have special characters, so put it in quotes and use regular cy.get
      cy.get(
        "[data-testid='data-category-user.derived.identifiable.unique_id']"
      );
    });

    it("Can render an edit form for a dataset collection with existing values", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-collection").click();
      cy.getByTestId("edit-drawer-content");
      cy.getByTestId("description-input").should(
        "have.value",
        "User information"
      );
      cy.getByTestId("identifiability-input").should("contain", "Identified");
      cy.getByTestId("selected-categories").children().should("have.length", 0);
    });

    it("Can render an edit form for a dataset with existing values", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-dataset").click();
      cy.getByTestId("edit-drawer-content");
      cy.getByTestId("name-input").should("have.value", "Demo Users Dataset");
      cy.getByTestId("description-input").should(
        "have.value",
        "Data collected about users for our analytics system."
      );
      cy.getByTestId("retention-input").should(
        "have.value",
        "30 days after account deletion"
      );
      cy.getByTestId("identifiability-input").should("contain", "Identified");
      cy.getByTestId("geography-input").should("contain", "Canada");
      cy.getByTestId("geography-input").should("contain", "United Kingdom");
      cy.getByTestId("selected-categories").children().should("have.length", 0);
    });
  });
});
