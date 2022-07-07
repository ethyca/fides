describe("Dataset", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
      "getDatasets"
    );
    cy.intercept("GET", "/api/v1/dataset/*", { fixture: "dataset.json" }).as(
      "getDataset"
    );
    cy.intercept("GET", "/api/v1/data_category", {
      fixture: "data_category.json",
    }).as("getDataCategory");
  });

  describe("List of datasets view", () => {
    it("Can navigate to the datasets list view", () => {
      cy.visit("/");
      cy.getByTestId("nav-link-Datasets").click();
      cy.wait("@getDatasets");
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
      cy.wait("@getDatasets");
      cy.getByTestId("load-dataset-btn").should("be.disabled");
      cy.getByTestId("dataset-row-demo_users_dataset").click();
      cy.getByTestId("load-dataset-btn").should("not.be.disabled");
      cy.getByTestId("load-dataset-btn").click();
      // for some reason this is slow in CI, so add a timeout :(
      cy.url({ timeout: 10000 }).should(
        "contain",
        "/dataset/demo_users_dataset"
      );
      cy.getByTestId("dataset-fields-table");
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
      cy.getByTestId("field-row-uuid")
        .click()
        .then(() => {
          cy.wait("@getDataset");
          cy.getByTestId("edit-drawer-content");
        });
      cy.getByTestId("input-description").should(
        "have.value",
        "User's unique ID"
      );
      cy.getByTestId("input-data_qualifier").should("contain", "Identified");
      cy.getByTestId("selected-categories").children().should("have.length", 1);
      cy.getByTestId("data-category-user.derived.identifiable.unique_id");
    });

    it("Can render an edit form for a dataset collection with existing values", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-collection")
        .click()
        .then(() => {
          cy.wait("@getDataset");
          cy.getByTestId("edit-drawer-content");
        });
      cy.getByTestId("input-description").should(
        "have.value",
        "User information"
      );
      cy.getByTestId("input-data_qualifier").should("contain", "Identified");
      cy.getByTestId("selected-categories").children().should("have.length", 0);
    });

    it("Can render an edit form for a dataset with existing values", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("more-actions-btn").click();
      cy.getByTestId("modify-dataset")
        .click()
        .then(() => {
          cy.wait("@getDataset");
          cy.getByTestId("edit-drawer-content");
        });
      cy.getByTestId("input-name").should("have.value", "Demo Users Dataset");
      cy.getByTestId("input-description").should(
        "have.value",
        "Data collected about users for our analytics system."
      );
      cy.getByTestId("input-retention").should(
        "have.value",
        "30 days after account deletion"
      );
      cy.getByTestId("input-data_qualifier").should("contain", "Identified");
      cy.getByTestId("input-third_country_transfers").should(
        "contain",
        "Canada"
      );
      cy.getByTestId("input-third_country_transfers").should(
        "contain",
        "United Kingdom"
      );
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
      cy.getByTestId("input-description").clear().type(newDescription);
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
      cy.getByTestId("input-description").clear().type(newDescription);
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
      cy.getByTestId("modify-dataset")
        .click()
        .then(() => {
          cy.getByTestId("input-description").clear().type(newDescription);
          cy.getByTestId("save-btn").click({ force: true });
          cy.wait("@putDataset").then((interception) => {
            const { body } = interception.request;
            expect(body.description).to.eql(newDescription);
          });
        });
    });
  });

  describe("Data category checkbox tree", () => {
    beforeEach(() => {
      cy.intercept("PUT", "/api/v1/dataset/*", { fixture: "dataset.json" }).as(
        "putDataset"
      );
    });
    it("Can render chosen data categories", () => {
      cy.visit("/dataset/demo_users");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      cy.get("[data-testid='checkbox-Unique ID'] > span").should(
        "have.attr",
        "data-checked"
      );
      const ancestors = [
        "User Data",
        "Derived Data",
        "Derived User Identifiable Data",
      ];
      ancestors.forEach((a) => {
        cy.get(`[data-testid='checkbox-${a}'] > span`).should(
          "have.attr",
          "data-indeterminate"
        );
      });
      cy.getByTestId("selected-categories").should(
        "contain",
        "user.derived.identifiable.unique_id"
      );
    });

    it("Can deselect data categories", () => {
      cy.visit("/dataset/demo_users");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("checkbox-Unique ID").click();
      // should collapse away
      cy.getByTestId("checkbox-Unique ID").should("not.exist");
      cy.get("[data-testid='checkbox-User Data'] > span").should(
        "not.have.attr",
        "data-indeterminate"
      );
      cy.getByTestId("done-btn").click();
      cy.getByTestId("selected-categories").should(
        "not.contain",
        "user.derived.identifiable.unique_id"
      );
      cy.getByTestId("save-btn").click({ force: true });
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[0].fields[5].data_categories).to.eql([]);
      });
    });

    it("Can select more data categories", () => {
      cy.visit("/dataset/demo_users");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("checkbox-Telemetry Data").click();
      cy.getByTestId("checkbox-Account Data").click();
      cy.getByTestId("done-btn").click();
      cy.getByTestId("selected-categories").should(
        "contain",
        "user.derived.identifiable.unique_id"
      );
      cy.getByTestId("selected-categories").should(
        "contain",
        "user.derived.identifiable.telemetry"
      );
      cy.getByTestId("selected-categories").should("contain", "account");
      cy.getByTestId("save-btn").click({ force: true });
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[0].fields[5].data_categories).to.eql([
          "user.derived.identifiable.unique_id",
          "user.derived.identifiable.telemetry",
          "account",
        ]);
      });
    });

    it("Can interact with the checkbox tree properly", () => {
      cy.visit("/dataset/demo_users");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      // expand account data
      cy.getByTestId("expand-Account Data").click();
      // select 1/2 children
      cy.getByTestId("checkbox-Account Contact Data").click();
      cy.get("[data-testid='checkbox-Account Contact Data'] > span").should(
        "have.attr",
        "data-checked"
      );
      // parent should be indeterminate since not all children are checked
      cy.get("[data-testid='checkbox-Account Data'] > span").should(
        "have.attr",
        "data-indeterminate"
      );
      // now select all children
      cy.getByTestId("checkbox-Payment Data").click();
      // parent should be checked since all children are checked
      cy.get("[data-testid='checkbox-Account Data'] > span").should(
        "have.attr",
        "data-checked"
      );
      // the children's children should be disabled and checked since the parent is selected
      cy.get("[data-testid='checkbox-Account City'] > span").should(
        "have.attr",
        "data-checked"
      );
      cy.get("[data-testid='checkbox-Account City'] > span").should(
        "have.attr",
        "data-disabled"
      );
      cy.getByTestId("done-btn").click();
      const expectedSelected = [
        "account.contact",
        "account.payment",
        "user.derived.identifiable.unique_id",
      ];
      expectedSelected.forEach((e) => {
        cy.getByTestId("selected-categories").should("contain", e);
      });
    });

    it("Should be able to clear selected", () => {
      cy.visit("/dataset/demo_users");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("checkbox-Account Data").click();
      cy.get("[data-testid='checkbox-Account Data'] > span").should(
        "have.attr",
        "data-checked"
      );
      cy.getByTestId("done-btn").click();
      cy.getByTestId("selected-categories").should(
        "contain",
        "user.derived.identifiable.unique_id"
      );
      cy.getByTestId("selected-categories").should("contain", "account");
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("clear-btn").click();
      cy.get("[data-testid='checkbox-Account Data'] > span").should(
        "not.have.attr",
        "data-checked"
      );
      cy.getByTestId("done-btn").click();
      cy.getByTestId("selected-categories").should(
        "not.contain",
        "user.derived.identifiable.unique_id"
      );
    });
  });
});
