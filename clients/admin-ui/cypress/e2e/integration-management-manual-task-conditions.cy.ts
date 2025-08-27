import { stubPlus } from "cypress/support/stubs";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

describe("Integration Management - Manual Task Conditions", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);

    // Mock config endpoint
    cy.intercept("GET", "/api/v1/config?api_set=false", {
      body: {},
    }).as("getConfig");

    // Mock connection endpoint
    cy.intercept("GET", "/api/v1/connection/demo_manual_task_integration", {
      fixture:
        "integration-management/manual-tasks/manual-task-connection.json",
    }).as("getConnection");

    // Mock manual task config endpoint with conditions
    cy.intercept("GET", "/api/v1/plus/connection/*/manual-task", {
      fixture: "integration-management/manual-tasks/task-config.json",
    }).as("getManualTask");

    // Mock dependency conditions endpoints
    cy.intercept(
      "PUT",
      "/api/v1/plus/connection/*/manual-task/dependency-conditions",
      {
        body: {},
      },
    ).as("updateDependencyConditions");

    // Mock dataset endpoints for DatasetReferencePicker
    cy.intercept(
      "GET",
      "/api/v1/dataset?minimal=true&exclude_saas_datasets=true",
      {
        fixture: "datasets.json",
      },
    ).as("getFilteredDatasets");

    cy.intercept("GET", "/api/v1/dataset/*", {
      fixture: "dataset.json",
    }).as("getDatasetByKey");

    // Navigate directly to conditions tab
    cy.visit(
      `${INTEGRATION_MANAGEMENT_ROUTE}/demo_manual_task_integration#conditions`,
    );
    cy.wait("@getConnection");
  });

  describe("Tab Access and Display", () => {
    it("should access the conditions tab and display existing conditions", () => {
      // Verify tab is active
      cy.getAntTab("Conditions")
        .parents(".ant-tabs-tab")
        .should("have.class", "ant-tabs-tab-active");

      // Verify existing conditions are displayed
      cy.getByTestId("conditions-list").should("exist");

      // Check that existing conditions from fixture are displayed
      cy.getByTestId("conditions-list")
        .find(".ant-list-item")
        .should("have.length", 2);
    });
  });

  describe("Add New Condition", () => {
    it("should handle exists/not exists operators correctly (value input disabled)", () => {
      cy.getByTestId("add-condition-btn").click();

      // Fill in the dataset reference picker
      cy.getByTestId("dataset-reference-picker").pickDatasetReference(
        "Demo Users Dataset",
        "users",
        "email",
      );

      // Test "Exists" operator
      cy.getByTestId("operator-select").antSelect("Exists");

      // Verify value input is disabled for "exists"
      cy.getByTestId("value-input").should("be.disabled");
      cy.getByTestId("value-input").should(
        "have.attr",
        "placeholder",
        "Not required",
      );

      // Test "Does not exist" operator
      cy.getByTestId("operator-select").antSelect("Does not exist");

      // Verify value input is disabled for "not exists"
      cy.getByTestId("value-input").should("be.disabled");
      cy.getByTestId("value-input").should(
        "have.attr",
        "placeholder",
        "Not required",
      );

      // Test that value input is enabled for other operators
      cy.getByTestId("operator-select").antSelect("Equals");
      cy.getByTestId("value-input").should("not.be.disabled");
      cy.getByTestId("value-input").should(
        "have.attr",
        "placeholder",
        "Enter value (text, number, or true/false)",
      );
    });

    it("should successfully add a new condition", () => {
      cy.getByTestId("add-condition-btn").click();

      // Fill in the dataset reference picker
      cy.getByTestId("dataset-reference-picker").pickDatasetReference(
        "Demo Users Dataset",
        "users",
        "uuid",
      );

      // Select operator
      cy.getByTestId("operator-select").antSelect("Equals");

      // Enter value
      cy.getByTestId("value-input").type("test_user_123");

      // Submit the form
      cy.getByTestId("save-btn").click();

      // Verify API call was made with correct parameters
      cy.wait("@updateDependencyConditions").then((interception) => {
        expect(interception.request.body).to.deep.equal([
          {
            logical_operator: "and",
            conditions: [
              {
                field_address: "asdas.asdas123",
                operator: "lt",
                value: 12,
              },
              {
                field_address: "asdasd",
                operator: "gte",
                value: "asdasd",
              },
              {
                field_address: "demo_users_dataset:users:uuid",
                operator: "eq",
                value: "test_user_123",
              },
            ],
          },
        ]);
      });

      // Verify success message
      cy.contains("Condition added successfully!").should("be.visible");
    });
  });

  describe("Edit Condition", () => {
    it("should open edit modal when edit button is clicked", () => {
      // Click edit button on first condition
      cy.getByTestId("edit-condition-0-btn").click();

      // Verify modal opens with editing mode
      cy.contains("Edit condition").should("be.visible");
      cy.contains("Update the condition settings for task creation.").should(
        "be.visible",
      );

      // Verify form is populated with existing values
      cy.getByTestId("operator-select").should("contain", "Less than");
      cy.getByTestId("value-input").should("have.value", "12");
    });

    it("should successfully update an existing condition", () => {
      // Click edit button on first condition
      cy.getByTestId("edit-condition-0-btn").click();

      // Change the operator
      cy.getByTestId("operator-select").antSelect("Greater than");

      // Change the value
      cy.getByTestId("value-input").clear().type("15");

      // Submit the form
      cy.getByTestId("save-btn").click();

      // Verify API call was made with correct parameters
      cy.wait("@updateDependencyConditions").then((interception) => {
        expect(interception.request.body).to.deep.equal([
          {
            logical_operator: "and",
            conditions: [
              {
                field_address: "asdas.asdas123",
                operator: "gt",
                value: 15,
              },
              {
                field_address: "asdasd",
                operator: "gte",
                value: "asdasd",
              },
            ],
          },
        ]);
      });

      // Verify success message
      cy.contains("Condition updated successfully!").should("be.visible");
    });
  });

  describe("Delete Condition", () => {
    it("should successfully delete a condition when confirmed", () => {
      // Click delete button on first condition
      cy.getByTestId("delete-condition-0-btn").click();

      // Confirm deletion
      cy.getByTestId("continue-btn").click();

      // Verify API call was made with remaining conditions
      cy.wait("@updateDependencyConditions").then((interception) => {
        expect(interception.request.body).to.deep.equal([
          {
            logical_operator: "and",
            conditions: [
              {
                field_address: "asdasd",
                operator: "gte",
                value: "asdasd",
              },
            ],
          },
        ]);
      });

      // Verify modal closes
      cy.getByTestId("confirmation-modal").should("not.exist");

      // Verify success message
      cy.contains("Condition deleted successfully!").should("be.visible");
    });
  });
});
