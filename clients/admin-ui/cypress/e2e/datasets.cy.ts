import {
  CONNECTION_STRING,
  stubDatasetCrud,
  stubPlus,
} from "cypress/support/stubs";

describe("Dataset", () => {
  beforeEach(() => {
    cy.login();
    stubDatasetCrud();
    // Ensure these tests all run with Plus features disabled.
    stubPlus(false);
  });

  describe("List of datasets view", () => {
    it("Can navigate to the datasets view via URL", () => {
      cy.visit("/dataset");
      cy.getByTestId("dataset-table");
    });

    it("Can navigate to the datasets list view", () => {
      cy.visit("/");
      cy.getByTestId("Manage datasets-nav-link").click();
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("dataset-table");
      cy.getByTestId("row-3");
    });

    it("Can edit a dataset from the list view / edit drawer", () => {
      cy.visit("/dataset");
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("row-0-col-actions").find("button").click();

      cy.getByTestId("input-name").should("have.value", "Demo Users Dataset");
      cy.getByTestId("input-description").should(
        "have.value",
        "Data collected about users for our analytics system.",
      );

      cy.getByTestId("input-name").clear().type("New dataset name");
      cy.getByTestId("input-description").clear().type("New description");
      cy.getByTestId("save-btn").click();

      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.name).to.eql("New dataset name");
        expect(body.description).to.eql("New description");
      });
    });

    it("Can delete a dataset from the list view / edit drawer", () => {
      cy.visit("/dataset");
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("row-0-col-actions").find("button").click();
      cy.getByTestId("delete-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteDataset").then((interception) => {
        expect(interception.request.url).to.contain("demo_users_dataset");
      });
      cy.getByTestId("toast-success-msg");
    });

    it("Can use the search bar to filter datasets", () => {
      cy.visit("/dataset");
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("dataset-table");
      cy.getByTestId("row-3");

      cy.getByTestId("dataset-search").type("postgres");
      cy.wait("@getFilteredDatasets").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("search=postgres");
      });
    });

    it("Can click on a row to navigate an dataset detail page", () => {
      cy.visit("/dataset");
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("row-0").click();
      cy.url().should("contain", "/dataset/demo_users_dataset");
      cy.getByTestId("collections-table");
    });
  });

  describe("Dataset Detail view", () => {
    it("Can navigate to edit a dataset via URL", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("collections-table");
    });

    it("Displays a table with the dataset's collections", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("collections-table");
      cy.getByTestId("row-0-col-name").contains("users");
      cy.getByTestId("row-1-col-name").contains("products");
    });

    it("Can use the search bar to filter collections", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("collections-table");
      cy.getByTestId("collections-search").type("products");
      cy.getByTestId("row-0-col-name").contains("products");
      cy.getByTestId("row-1-col-name").should("not.exist");
    });

    it("Can edit a collection from the dataset view", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("row-0-col-actions").find("button").click();
      cy.getByTestId("edit-drawer-content");
      cy.getByTestId("input-description").should(
        "have.value",
        "User information",
      );

      cy.getByTestId("input-description")
        .clear()
        .type("New description", { delay: 25 });

      cy.getByTestId("save-btn").click();

      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[0].description).to.eql("New description");
      });
    });

    it("Can delete a collection from the dataset view", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("row-0-col-actions").find("button").click();
      cy.getByTestId("delete-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections.length).to.eql(2);
      });
    });

    it("Can navigate to a collection's fields view", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("row-0-col-name").click();
      cy.getByTestId("fields-table");
    });
  });

  describe("Collection fields view", () => {
    it("Can navigate to a collection's fields view via URL", () => {
      cy.visit("/dataset/demo_users_dataset/users");
      cy.getByTestId("fields-table");
    });

    it("Displays a table with the collection's fields", () => {
      cy.visit("/dataset/demo_users_dataset/users");
      cy.getByTestId("fields-table");
      cy.getByTestId("row-4-col-name").contains("state");
      cy.getByTestId("row-5").contains("uuid");
    });

    it("Can use the search bar to filter fields", () => {
      cy.visit("/dataset/demo_users_dataset/users");
      cy.getByTestId("fields-table");
      cy.getByTestId("fields-search").type("uuid");
      cy.getByTestId("row-0-col-name").contains("uuid");
      cy.getByTestId("row-1-col-name").should("not.exist");
    });

    describe("Data category checkbox tree", () => {
      it("Can render chosen data categories", () => {
        cy.visit("/dataset/demo_users_dataset/users");
        cy.getByTestId("row-5-col-actions").find("button").click();

        cy.getByTestId("data-category-dropdown").click();
        cy.get("[data-testid='checkbox-Unique ID'] > span").should(
          "have.attr",
          "data-checked",
        );
        cy.get(`[data-testid='checkbox-User Data'] > span`).should(
          "have.attr",
          "data-indeterminate",
        );
        cy.getByTestId("selected-categories").should(
          "contain",
          "user.unique_id",
        );
      });

      it.only("Can deselect data categories", () => {
        cy.visit("/dataset/demo_users_dataset/users");
        cy.getByTestId("row-5-col-actions").find("button").click();

        cy.getByTestId("data-category-dropdown").click();
        cy.getByTestId("checkbox-Unique ID").click();
        // should collapse away
        cy.getByTestId("checkbox-Unique ID").should("not.exist");
        cy.get("[data-testid='checkbox-User Data'] > span").should(
          "not.have.attr",
          "data-indeterminate",
        );
        cy.getByTestId("data-category-done-btn").click();
        cy.getByTestId("selected-categories").should(
          "not.contain",
          "user.derived.identifiable.unique_id",
        );
        cy.getByTestId("save-btn").click({ force: true });
        cy.wait("@putDataset").then((interception) => {
          const { body } = interception.request;
          expect(body.collections[0].fields[5].data_categories).to.eql([]);
        });
      });

      it("Can select more data categories", () => {
        cy.visit("/dataset/demo_users_dataset");
        cy.getByTestId("row-5-col-actions").find("button").click();
        cy.getByTestId("data-category-dropdown").click();
        cy.getByTestId("checkbox-Telemetry Data").click();
        cy.getByTestId("checkbox-System Data").click();
        cy.getByTestId("data-category-done-btn").click();
        cy.getByTestId("selected-categories").should(
          "contain",
          "user.unique_id",
        );
        cy.getByTestId("selected-categories").should(
          "contain",
          "user.telemetry",
        );
        cy.getByTestId("selected-categories").should("contain", "system");
        cy.getByTestId("save-btn").click({ force: true });
        cy.wait("@putDataset").then((interception) => {
          const { body } = interception.request;
          expect(body.collections[0].fields[5].data_categories).to.eql([
            "user.unique_id",
            "user.telemetry",
            "system",
          ]);
        });
      });

      it("Can interact with the checkbox tree properly", () => {
        cy.visit("/dataset/demo_users_dataset");
        cy.getByTestId("row-5-col-actions").find("button").click();
        cy.getByTestId("data-category-dropdown").click();
        // expand system data
        cy.getByTestId("expand-System Data").click();
        // select 1/2 children
        cy.getByTestId("checkbox-Authentication Data").click();
        cy.get("[data-testid='checkbox-Authentication Data'] > span").should(
          "have.attr",
          "data-checked",
        );
        // parent should be indeterminate since not all children are checked
        cy.get("[data-testid='checkbox-System Data'] > span").should(
          "have.attr",
          "data-indeterminate",
        );
        // now select all children
        cy.getByTestId("checkbox-Operations Data").click();
        // parent should be checked since all children are checked
        cy.get("[data-testid='checkbox-System Data'] > span").should(
          "have.attr",
          "data-checked",
        );
        // the children of selected parents should be disabled
        cy.getByTestId("checkbox-Authorization Information").click();
        cy.get("[data-testid='checkbox-Account password'] > span").should(
          "have.attr",
          "data-checked",
        );
        cy.get("[data-testid='checkbox-Biometric Credentials'] > span").should(
          "have.attr",
          "data-disabled",
        );
        cy.get("[data-testid='checkbox-Password'] > span").should(
          "have.attr",
          "data-disabled",
        );
        cy.getByTestId("data-category-done-btn").click();
        const expectedSelected = [
          "system.authentication",
          "system.operations",
          "user.authorization",
        ];
        expectedSelected.forEach((e) => {
          cy.getByTestId("selected-categories").should("contain", e);
        });
      });

      it("Should be able to clear selected", () => {
        cy.visit("/dataset/demo_users_dataset");
        cy.getByTestId("row-5-col-actions").find("button").click();
        cy.getByTestId("data-category-dropdown").click();
        cy.getByTestId("checkbox-System Data").click();
        cy.get("[data-testid='checkbox-System Data'] > span").should(
          "have.attr",
          "data-checked",
        );
        cy.getByTestId("data-category-done-btn").click();
        cy.getByTestId("selected-categories").should(
          "contain",
          "user.unique_id",
        );
        cy.getByTestId("selected-categories").should("contain", "system");
        cy.getByTestId("data-category-dropdown").click();
        cy.getByTestId("data-category-clear-btn").click();
        cy.get("[data-testid='checkbox-System Data'] > span").should(
          "not.have.attr",
          "data-checked",
        );
        cy.getByTestId("data-category-done-btn").click();
        cy.getByTestId("selected-categories").should(
          "not.contain",
          "user.unique_id",
        );
      });
    });
  });

  describe("Creating datasets", () => {
    it("Can render the create dataset page", () => {
      cy.visit("/dataset");
      cy.getByTestId("create-dataset-btn").click();
      cy.url().should("contain", "/dataset/new");
      cy.getByTestId("upload-yaml-btn");
      cy.getByTestId("connect-db-btn");
    });
  });
});
