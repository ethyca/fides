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

    it("Can edit a dataset YAML from the list view / edit drawer", () => {
      cy.visit("/dataset");
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("row-0-col-actions").find("button").click();
      cy.getByTestId("edit-yaml-btn").click();
      cy.getByTestId("yaml-editor-section").should("be.visible");
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

      // YAML editing is available only at the top dataset level
      cy.getByTestId("edit-yaml-btn").should("not.exist");

      cy.getByTestId("input-description")
        .clear()
        .type("New description", { delay: 25 });

      cy.getByTestId("save-btn").click();

      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[0].description).to.eql("New description");
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

    it("Can navigate to a subfields view", () => {
      cy.visit("/dataset/demo_users_dataset/users");
      cy.getByTestId("row-6").contains("workplace_info").click();
      cy.url().should(
        "contain",
        "/dataset/demo_users_dataset/users/workplace_info",
      );
      cy.getByTestId("fields-table");
    });
  });

  describe("Subfields view", () => {
    it("Can navigate to a subfields view via URL", () => {
      cy.visit("/dataset/demo_users_dataset/users/workplace_info");
      cy.getByTestId("fields-table");
    });

    it("Displays a table with the subfields", () => {
      cy.visit("/dataset/demo_users_dataset/users/workplace_info");
      cy.getByTestId("fields-table");
      cy.getByTestId("row-0-col-name").contains("employer");
      cy.getByTestId("row-1-col-name").contains("position");
      cy.getByTestId("row-2-col-name").contains("direct_reports");
    });

    it("Can use the search bar to filter subfields", () => {
      cy.visit("/dataset/demo_users_dataset/users/workplace_info");
      cy.getByTestId("fields-table");
      cy.getByTestId("fields-search").type("position");
      cy.getByTestId("row-0-col-name").contains("position");
      cy.getByTestId("row-1-col-name").should("not.exist");
    });

    it("Can navigate to a level deeper in nested fields", () => {
      cy.visit("/dataset/demo_users_dataset/users/workplace_info");
      cy.getByTestId("row-0-col-name").contains("employer").click();
      cy.url().should(
        "contain",
        "/dataset/demo_users_dataset/users/workplace_info/employer",
      );
      cy.getByTestId("fields-table");
      cy.getByTestId("row-0-col-name").contains("name");
      cy.getByTestId("row-1-col-name").contains("address");
      cy.getByTestId("row-2-col-name").contains("phone");
    });

    it("Can navigate deeply nested fields with unexpected names", () => {
      cy.visit(
        "/dataset/example_dataset_issue_hj36/example_table/example_nested_field/example_failure_nested_field.1",
      );
      cy.getByTestId("row-0-col-name")
        .contains("some.thing/Stupid-that's_redicuLous&")
        .click();
      cy.url().should(
        "contain",
        "/dataset/example_dataset_issue_hj36/example_table/example_nested_field/example_failure_nested_field.1/some.thing%2FStupid-that's_redicuLous%26",
      );
      cy.getByTestId("fields-table");
      cy.getByTestId("row-0-col-name").contains("another.dumb:th!ng");
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
