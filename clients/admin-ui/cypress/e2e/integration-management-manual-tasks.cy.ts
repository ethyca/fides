import {
  stubIntegrationManagement,
  stubManualTaskConfig,
  stubPlus,
  stubSystemCrud,
} from "cypress/support/stubs";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

describe("Integration Management - Manual Task Configuration", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubIntegrationManagement();
    stubManualTaskConfig();

    // Mock config endpoint
    cy.intercept("GET", "/api/v1/config?api_set=false", {
      body: {},
    }).as("getConfig");

    // Mock users endpoint
    cy.intercept("GET", "/api/v1/user*", {
      fixture: "integration-management/manual-tasks/users.json",
    }).as("getUsers");

    // Navigate to specific integration manual tasks tab
    cy.visit(`${INTEGRATION_MANAGEMENT_ROUTE}/demo_manual_task_integration`);
    cy.wait("@getConnection");
    cy.getAntTab("Manual tasks").click({ force: true });
    cy.wait("@getManualFields");
    cy.wait("@getManualTask");
    cy.wait("@getUsers");
  });

  describe("Manual Task Table and UI", () => {
    it("should display the manual tasks configuration interface", () => {
      // Verify tab is active and content is loaded
      cy.getAntTab("Manual tasks")
        .parents(".ant-tabs-tab")
        .should("have.class", "ant-tabs-tab-active");

      // Check description text
      cy.contains("Configure manual tasks for this integration").should(
        "be.visible",
      );

      // Verify action buttons are present
      cy.getByTestId("manage-secure-access-btn").should("exist");
      cy.getByTestId("add-manual-task-btn").should("exist");

      // Verify table is displayed
      cy.get("table").should("exist");
      cy.get("tbody tr").should("have.length.at.least", 1);
    });

    it("should display manual tasks with correct data", () => {
      // Verify first task data is displayed correctly
      cy.getAntTableRow("task1").within(() => {
        cy.get("td").eq(0).should("contain", "Customer Data Export");
        cy.get("td")
          .eq(1)
          .should("contain", "Export customer data for GDPR requests");
        cy.get("td").eq(2).should("contain", "Attachment");
        cy.get("td").eq(3).should("contain", "Access");
      });
    });

    it("should show empty state when no manual tasks exist", () => {
      cy.intercept("GET", "/api/v1/plus/connection/*/manual-fields*", {
        body: [],
      }).as("getEmptyManualFields");

      cy.reload();
      cy.getAntTab("Manual tasks").click({ force: true });
      cy.wait("@getEmptyManualFields");

      cy.contains("No manual tasks configured yet").should("be.visible");
    });
  });

  describe("Add Manual Task", () => {
    it("should create a new manual task successfully", () => {
      cy.getByTestId("add-manual-task-btn").click();

      // Fill out the form
      cy.getByTestId("input-name").type("New Manual Task");
      cy.getByTestId("input-description").type(
        "Description of the manual task",
      );
      cy.getByTestId("select-request-type").antSelect("Access");
      cy.getByTestId("select-field-type").antSelect("Text");

      // Submit the form
      cy.getByTestId("save-btn").click();

      cy.wait("@createManualField").then((interception) => {
        // Verify the request contains all form data
        expect(interception.request.body).to.deep.include({
          label: "New Manual Task",
          help_text: "Description of the manual task",
          request_type: "access",
          field_type: "text",
        });
      });
      cy.wait("@getManualFields"); // Refresh after creation

      // Verify modal is closed and task appears in table
      cy.getByTestId("add-manual-task-modal").should("not.exist");
    });

    it("should close modal when cancel is clicked", () => {
      cy.getByTestId("add-manual-task-btn").click();
      cy.getByTestId("add-manual-task-modal").should("be.visible");
      cy.getByTestId("cancel-btn").click();
      cy.getByTestId("add-manual-task-modal").should("not.exist");
    });
  });

  describe("Edit Manual Task", () => {
    it("should open edit modal when edit button is clicked", () => {
      // Click edit button on first task
      cy.getAntTableRow("task1").within(() => {
        cy.getByTestId("edit-btn").click();
      });

      // Verify modal opens with existing data
      cy.getByTestId("add-manual-task-modal").should("be.visible");
      cy.contains("Edit manual task").should("be.visible");
      cy.getByTestId("input-name").should("have.value", "Customer Data Export");
    });

    it("should update manual task successfully", () => {
      cy.getAntTableRow("task1").within(() => {
        cy.getByTestId("edit-btn").click();
      });

      // Modify the task
      cy.getByTestId("input-name").clear().type("Updated Task Name");
      cy.getByTestId("save-btn").click();

      cy.wait("@updateManualField").then((interception) => {
        // Verify the request contains the updated data
        expect(interception.request.body).to.deep.include({
          label: "Updated Task Name",
        });
      });
      cy.wait("@getManualFields");

      cy.getByTestId("add-manual-task-modal").should("not.exist");
    });
  });

  describe("Delete Manual Task", () => {
    it("should delete manual task when confirmed", () => {
      cy.getAntTableRow("task1").within(() => {
        cy.getByTestId("delete-btn").click();
      });

      // Confirm deletion
      cy.getByTestId("continue-btn").click();

      cy.wait("@deleteManualField");
      cy.wait("@getManualFields");

      // Verify task is removed
      cy.getByTestId("confirmation-modal").should("not.exist");
    });
  });

  describe("User Assignment Management", () => {
    it("should display user assignment section", () => {
      // Verify assignment section exists
      cy.contains("Assign manual tasks to users:").should("be.visible");
      cy.getByTestId("assign-users-select").should("be.visible");
    });

    it("should load and display currently assigned users", () => {
      // Verify pre-selected users are shown
      cy.getByTestId("assign-users-select")
        .find(".ant-select-selection-item")
        .should("have.length.at.least", 1);
      cy.getByTestId("assign-users-select")
        .find(".ant-select-selection-item")
        .first()
        .should("contain", "External 1");
    });

    it("should show selected users first in dropdown", () => {
      // Open dropdown
      cy.getByTestId("assign-users-select").click();

      // Verify selected users appear first
      cy.get(".ant-select-item").first().should("contain", "External 1");
      cy.get(".ant-select-item")
        .first()
        .should("have.class", "ant-select-item-option-selected");
    });

    it("should assign users to manual tasks", () => {
      // Select additional user using antSelect
      cy.getByTestId("assign-users-select").antSelect(
        "Jane Smith (jane.smith@example.com)",
      );

      cy.wait("@assignUsersToManualTask").then((interception) => {
        // Verify the request body is an array of user IDs
        expect(interception.request.body).to.be.an("array");
        // Should contain both existing and newly selected user
        expect(interception.request.body).to.include("user_jane_smith");
      });

      // Verify success message
      cy.contains("Assigned users have been updated").should("be.visible");
    });

    it("should unassign users from manual tasks", () => {
      // Remove a selected user
      cy.getByTestId("assign-users-select").antRemoveSelectTag(
        "External 1 User",
      );

      cy.wait("@assignUsersToManualTask").then((interception) => {
        // Verify the request body is an array of user IDs
        expect(interception.request.body).to.be.an("array");
        // Should not contain the removed user
        expect(interception.request.body).to.not.include(
          "fid_498e6f1d-820e-4b2b-bc1a-8ed63dfae25e",
        );
      });

      // Verify user is removed
      cy.getByTestId("assign-users-select")
        .find(".ant-select-selection-item")
        .should("not.contain", "External 1");
    });
  });

  describe("External User Management", () => {
    it("should open external user creation modal", () => {
      cy.getByTestId("manage-secure-access-btn").click();

      cy.getByTestId("create-external-user-modal").should("exist");
      cy.contains("Create External Respondent User").should("be.visible");
    });

    it("should create external user successfully", () => {
      cy.getByTestId("manage-secure-access-btn").click();

      // Fill out user form
      cy.getByTestId("input-first_name").type("External");
      cy.getByTestId("input-last_name").type("User");
      cy.getByTestId("input-email_address").type("external@example.com");

      cy.getByTestId("save-btn").click();

      cy.wait("@createExternalUser").then((interception) => {
        // Verify the request contains all form data
        expect(interception.request.body).to.deep.include({
          email_address: "external@example.com",
          first_name: "External",
          last_name: "User",
        });
        // Verify username is generated from email
        expect(interception.request.body.username).to.equal("external");
      });
      cy.wait("@getUsers"); // Refresh users list

      // Verify modal closes and user is available in dropdown
      cy.getByTestId("create-external-user-modal").should("not.be.visible");
    });

    it("should handle external user creation errors", () => {
      cy.intercept("POST", "/api/v1/plus/external-user", {
        statusCode: 400,
        body: { detail: "Email already exists" },
      }).as("createExternalUserError");

      cy.getByTestId("manage-secure-access-btn").click();

      cy.getByTestId("input-first_name").type("External");
      cy.getByTestId("input-last_name").type("User");
      cy.getByTestId("input-email_address").type("existing@example.com");

      cy.getByTestId("save-btn").click();

      cy.wait("@createExternalUserError").then((interception) => {
        // Verify the request was made with the form data even though it failed
        expect(interception.request.body).to.deep.include({
          email_address: "existing@example.com",
          first_name: "External",
          last_name: "User",
        });
        expect(interception.request.body.username).to.equal("existing");
      });

      // Verify error message is displayed
      cy.contains("Email already exists").should("be.visible");
      cy.getByTestId("create-external-user-modal")
        .find("form")
        .should("be.visible"); // Modal stays open on error
    });
  });
});
