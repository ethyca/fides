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
    it("Can navigate to the datasets list view", () => {
      cy.visit("/");
      cy.getByTestId("Manage datasets-nav-link").click();
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("dataset-table");
      cy.getByTestId("row-3");

      // The classifier toggle should not be available.
      cy.get("input-classify").should("not.exist");

      cy.getByTestId("dataset-table__status-table-header").should("not.exist");
      cy.getByTestId("classification-status-badge").should("not.exist");
    });

    it("Can navigate to the datasets view via URL", () => {
      cy.visit("/dataset");
      cy.getByTestId("dataset-table");
    });

    it("Can load an individual dataset", () => {
      cy.visit("/dataset");
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("row-0").click();
      // for some reason this is slow in CI, so add a timeout :(
      cy.url({ timeout: 10000 }).should(
        "contain",
        "/dataset/demo_users_dataset",
      );
      cy.getByTestId("dataset-fields-table");
    });
  });

  describe("Dataset fields view", () => {
    it("Can navigate to edit a dataset via URL", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("dataset-fields-table");
    });

    it("Can choose different columns to view", () => {
      const columnNames = [
        "Field Name",
        "Description",
        "Personal Data Categories",
        "Identifiability",
      ];
      cy.visit("/dataset/demo_users_dataset");
      // check we can remove a column
      cy.getByTestId(`column-${columnNames[0]}`);
      cy.getByTestId("column-dropdown").click();
      cy.getByTestId(`checkbox-${columnNames[0]}`).click();
      cy.getByTestId(`column-${columnNames[0]}`).should("not.exist");

      // check we can clear all columns
      cy.getByTestId("column-clear-btn").click();
      columnNames.forEach((c) => {
        cy.getByTestId(`column-${c}`).should("not.exist");
      });

      // check we can add a column back
      cy.getByTestId(`checkbox-${columnNames[1]}`).click({ force: true });
      cy.getByTestId(`column-${columnNames[1]}`);

      // clicking 'done' should close the modal
      cy.getByTestId("column-done-btn").click();
      cy.getByTestId(`checkbox-${columnNames[0]}`).should("not.be.visible");
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
        "User's unique ID",
      );
      cy.getByTestId("selected-categories").children().should("have.length", 1);
      cy.getByTestId("taxonomy-entity-user.unique_id");
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
        "User information",
      );
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
        "Data collected about users for our analytics system.",
      );
      cy.getByTestId("selected-categories").children().should("have.length", 0);
    });
  });

  describe("Can edit datasets", () => {
    it("Can edit dataset fields", () => {
      const newDescription = "new description";
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("collection-select").select("products");
      cy.getByTestId("field-row-name").click();
      cy.getByTestId("input-description").clear().type(newDescription);

      // Updating the dataset will trigger a refresh of the GET request.
      cy.fixture("dataset.json").then((draftDataset) => {
        draftDataset.collections[1].fields[1].description = newDescription;
        cy.intercept("GET", "/api/v1/dataset/*", {
          body: { ...draftDataset },
        }).as("getDataset");
      });

      cy.getByTestId("save-btn").click({ force: true });

      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[1].fields[1].description).to.eql(
          newDescription,
        );
      });
      cy.wait("@getDataset");

      // The same dataset that was being edited should be shown in the table, updated.
      cy.getByTestId("edit-drawer-content").should("not.exist");
      cy.getByTestId("field-row-name").should("contain", newDescription);
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
        .click({ force: true })
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

  describe("Deleting datasets", () => {
    it("Can delete a field from a dataset", () => {
      const fieldName = "uuid";
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId(`field-row-${fieldName}`)
        .click()
        .then(() => {
          cy.getByTestId("delete-btn").click();
          cy.getByTestId("continue-btn").click();
          cy.wait("@putDataset").then((interception) => {
            const { body } = interception.request;
            expect(body.collections[0].fields.length).to.eql(5);
            expect(
              body.collections[0].fields.filter((f) => f.name === fieldName)
                .length,
            ).to.eql(0);
          });
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
          body.collections.filter((c) => c.name === collectionName).length,
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

  describe("Creating datasets", () => {
    it("Can render the create dataset page", () => {
      cy.visit("/dataset");
      cy.getByTestId("create-dataset-btn").click();
      cy.url().should("contain", "/dataset/new");
      cy.getByTestId("upload-yaml-btn");
      cy.getByTestId("connect-db-btn");
    });

    // TODO: Update to include the @monaco-editor/react component
    it.skip("Can create a dataset via yaml", () => {
      cy.visit("/dataset/new");
      cy.getByTestId("upload-yaml-btn").click();
      cy.fixture("dataset.json").then((dataset) => {
        const key = dataset.fides_key;
        const datasetAsString = JSON.stringify(dataset);
        // Cypress doesn't have a native "paste" command, so instead do change the value directly
        // (.type() is too slow, even with 0 delay)
        cy.getByTestId("input-yaml")
          .click()
          .invoke("val", datasetAsString)
          .trigger("change");
        // type just one space character to make sure the text field triggers Formik's handlers
        cy.getByTestId("input-yaml").type(" ");

        cy.getByTestId("submit-yaml-btn").click();
        cy.wait("@postDataset").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql(dataset);
        });

        // should navigate to the created dataset
        cy.getByTestId("toast-success-msg");
        cy.url().should("contain", `dataset/${key}`);
      });
    });

    // TODO: Update to include the @monaco-editor/react component
    it.skip("Can render errors in yaml", () => {
      cy.intercept("POST", "/api/v1/dataset", {
        statusCode: 422,
        body: {
          detail: [
            {
              loc: ["body", "fides_key"],
              msg: "field required",
              type: "value_error.missing",
            },
            {
              loc: ["body", "collections"],
              msg: "field required",
              type: "value_error.missing",
            },
          ],
        },
      }).as("postDataset");
      cy.visit("/dataset/new");
      cy.getByTestId("upload-yaml-btn").click();
      // type something that isn't yaml
      cy.getByTestId("input-yaml").type("invalid: invalid: invalid");
      cy.getByTestId("submit-yaml-btn").click();
      cy.getByTestId("error-yaml").should("contain", "Could not parse");

      // type something that is valid yaml and let backend render an error
      cy.getByTestId("input-yaml")
        .clear()
        .type("valid yaml that is not a dataset");
      cy.getByTestId("submit-yaml-btn").click();
      cy.getByTestId("error-yaml").should("contain", "field required");
    });

    it.skip("Can create a dataset by connecting to a database", () => {
      // workflow will be deprecated soon, disabled now with d&d
      cy.intercept("POST", "/api/v1/generate", {
        fixture: "generate/dataset.json",
      }).as("postGenerate");

      cy.visit("/dataset/new");
      cy.getByTestId("connect-db-btn").click();
      cy.getByTestId("input-url").type(CONNECTION_STRING);
      cy.getByTestId("create-dataset-btn").click();
      cy.wait("@postGenerate").then((interception) => {
        expect(
          interception.request.body.generate.config.connection_string,
        ).to.eql(CONNECTION_STRING);
      });
      cy.wait("@postDataset").then((interception) => {
        // should be whatever is in the generate fixture
        expect(interception.request.body.fides_key).to.eql("public");
      });
      // should navigate to the created dataset
      cy.getByTestId("toast-success-msg");
      cy.url().should("contain", `dataset/demo_users_dataset`);
    });

    it.skip("Can create a multiple datasets generated by connecting to a database", () => {
      // workflow will be deprecated soon, disabled now with d&d
      const connectionString =
        "postgresql://postgres:fidesctl@fidesctl-db:5432/fidesctl_test";
      cy.fixture("generate/dataset.json").then(
        ({ generate_results: [dataset] }) => {
          cy.intercept("POST", "/api/v1/generate", {
            body: {
              generate_results: [
                { ...dataset, fides_key: "generated-1" },
                { ...dataset, fides_key: "generated-2" },
              ],
            },
          }).as("postGenerate");
        },
      );

      cy.visit("/dataset/new");
      cy.getByTestId("connect-db-btn").click();
      cy.getByTestId("input-url").type(connectionString);
      cy.getByTestId("create-dataset-btn").click();
      cy.wait("@postGenerate").then((interception) => {
        expect(
          interception.request.body.generate.config.connection_string,
        ).to.eql(connectionString);
      });

      // Two requests should be intercepted.
      cy.wait(["@postDataset", "@postDataset"]).then((interceptions) => {
        const generatedKeys = interceptions.map(
          (i) => i.request.body.fides_key,
        );
        expect(generatedKeys.sort()).to.eql(["generated-1", "generated-2"]);
      });

      // Should navigate to the first created dataset.
      cy.getByTestId("toast-success-msg");
      cy.url().should("contain", `dataset/demo_users_dataset`);
    });

    it.skip("Can render errors when connecting to a database", () => {
      // workflow will be deprecated soon, disabled now with d&d
      // Update error after #892 when backend gives better errors than 500
      cy.intercept("POST", "/api/v1/generate", {
        statusCode: 500,
        body: {
          status: "PARSING_ERROR",
          originalStatus: 500,
          data: "Internal Server Error",
          error: "SyntaxError: Unexpected token I in JSON at position 0",
        },
      }).as("postGenerate");

      cy.visit("/dataset/new");
      cy.getByTestId("connect-db-btn").click();

      // verify need something in the URL box
      cy.getByTestId("create-dataset-btn").click();
      cy.getByTestId("error-url").should("contain", "required");

      // First ensure that a Generate error shows the error toast
      cy.getByTestId("input-url").type("mock-url");
      cy.getByTestId("create-dataset-btn").click();
      cy.wait("@postGenerate");
      cy.getByTestId("toast-error-msg");

      // Then ensure a Dataset Create error shows the error toast
      cy.intercept("POST", "/api/v1/generate", {
        fixture: "generate/dataset.json",
      }).as("postGenerate");
      cy.intercept("POST", "/api/v1/dataset", {
        statusCode: 422,
        body: {
          detail: [
            {
              loc: ["body", "fides_key"],
              msg: "field required",
              type: "value_error.missing",
            },
            {
              loc: ["body", "collections"],
              msg: "field required",
              type: "value_error.missing",
            },
          ],
        },
      }).as("postDataset");
      cy.getByTestId("input-url").type("mock-url");
      cy.getByTestId("create-dataset-btn").click();
      cy.wait("@postGenerate");
      cy.wait("@postDataset");
      cy.getByTestId("toast-error-msg");
    });
  });

  describe("Data category checkbox tree", () => {
    it("Can render chosen data categories", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      cy.get("[data-testid='checkbox-Unique ID'] > span").should(
        "have.attr",
        "data-checked",
      );
      cy.get(`[data-testid='checkbox-User Data'] > span`).should(
        "have.attr",
        "data-indeterminate",
      );
      cy.getByTestId("selected-categories").should("contain", "user.unique_id");
    });

    it("Can deselect data categories", () => {
      cy.visit("/dataset/demo_users_dataset");
      cy.getByTestId("field-row-uuid").click();
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
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("checkbox-Telemetry Data").click();
      cy.getByTestId("checkbox-System Data").click();
      cy.getByTestId("data-category-done-btn").click();
      cy.getByTestId("selected-categories").should("contain", "user.unique_id");
      cy.getByTestId("selected-categories").should("contain", "user.telemetry");
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
      cy.getByTestId("field-row-uuid").click();
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
      cy.getByTestId("field-row-uuid").click();
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("checkbox-System Data").click();
      cy.get("[data-testid='checkbox-System Data'] > span").should(
        "have.attr",
        "data-checked",
      );
      cy.getByTestId("data-category-done-btn").click();
      cy.getByTestId("selected-categories").should("contain", "user.unique_id");
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
