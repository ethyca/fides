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

    it("Can choose a different collection", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("field-row-price").should("not.exist");
      cy.getByTestId("collection-select").select("products");
      cy.getByTestId("field-row-price").should("exist");
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

  describe("Can edit datasets", () => {
    beforeEach(() => {
      cy.intercept("PUT", "/api/v1/dataset/*", { fixture: "dataset.json" }).as(
        "putDataset"
      );
    });
    it("Can edit dataset fields", () => {
      const newDescription = "new description";
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("description-input").clear().type(newDescription);
      cy.getByTestId("save-btn").click({ force: true });
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[0].fields[5].description).to.eql(
          newDescription
        );
      });
    });

    it("Can edit dataset collections", () => {
      const newDescription = "new collection description";
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("collection-select").select("products");
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-collection").click();
      cy.getByTestId("description-input").clear().type(newDescription);
      cy.getByTestId("save-btn").click({ force: true });
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[1].description).to.eql(newDescription);
      });
    });

    it("Can edit datasets", () => {
      const newDescription = "new dataset description";
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("collection-select").select("products");
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-dataset").click();
      cy.getByTestId("description-input").clear().type(newDescription);
      cy.getByTestId("save-btn").click({ force: true });
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.description).to.eql(newDescription);
      });
    });
  });

  describe("Deleting datasets", () => {
    beforeEach(() => {
      cy.intercept("PUT", "/api/v1/dataset/*").as("putDataset");
      cy.fixture("dataset.json").then((dataset) => {
        cy.intercept("DELETE", "/api/v1/dataset/*", {
          body: {
            message: "resource deleted",
            resource: dataset,
          },
        }).as("deleteDataset");
      });
    });

    it("Can delete a field from a dataset", () => {
      const fieldName = "uuid";
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId(`field-row-${fieldName}`).click();
      cy.getByTestId("delete-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[0].fields.length).to.eql(5);
        expect(
          body.collections[0].fields.filter((f) => f.name === fieldName).length
        ).to.eql(0);
      });
    });

    it("Can delete a collection from a dataset", () => {
      const collectionName = "users";
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("collection-select").select(collectionName);
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-collection").click();
      cy.getByTestId("delete-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections.length).to.eql(1);
        expect(
          body.collections.filter((c) => c.name === collectionName).length
        ).to.eql(0);
      });
    });

    it("Can delete a dataset", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-dataset").click();
      cy.getByTestId("delete-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteDataset").then((interception) => {
        expect(interception.request.url).to.contain("demo_users_dataset");
      });
      cy.getByTestId("toast-success-msg");
    });
  });
});
