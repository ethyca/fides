import { API_URL } from "../support/constants";

describe("External Manual Tasks", () => {
  beforeEach(() => {
    // Mock external auth API endpoints
    cy.intercept("POST", `${API_URL}/external-login/request-otp`, {
      body: {
        message: "OTP code sent to email",
        email: "john.doe@example.com",
      },
    }).as("postRequestOtp");

    cy.intercept("POST", `${API_URL}/external-login/verify-otp`, {
      body: {
        user_data: {
          id: "ext_user_123",
          username: "john.doe.external",
          created_at: "2025-06-17T20:17:08.391Z",
          email_address: "john.doe@example.com",
          first_name: "John",
          last_name: "Doe",
          disabled: false,
          disabled_reason: "",
        },
        token_data: {
          access_token: "ext_token_abc123def456",
        },
      },
    }).as("postVerifyOtp");

    // Mock external tasks API endpoints
    cy.intercept("GET", `${API_URL}/manual-tasks*`, {
      fixture: "external-manual-tasks/user-tasks.json",
    }).as("getExternalTasks");

    cy.intercept("POST", `${API_URL}/manual-tasks/*/complete`, {
      fixture: "external-manual-tasks/complete-task-success.json",
    }).as("completeExternalTask");

    cy.intercept("POST", `${API_URL}/manual-tasks/*/skip`, {
      fixture: "external-manual-tasks/skip-task-success.json",
    }).as("skipExternalTask");

    // Mock mixed status tasks for action visibility tests
    cy.intercept("GET", `${API_URL}/manual-tasks*status*`, {
      fixture: "external-manual-tasks/mixed-status-tasks.json",
    }).as("getMixedStatusTasks");
  });

  describe("Authentication Flow", () => {
    it("should complete full OTP authentication and show tasks", () => {
      cy.visit("/manual-tasks-external?token=test_token_123");

      // Step 1: Should show OTP request form
      cy.get('[data-testid="external-auth-container"]').should("be.visible");
      cy.get('[data-testid="otp-request-form"]').should("be.visible");
      cy.get('[data-testid="otp-request-email-display"]')
        .should("be.visible")
        .and("contain", "user@example.com");

      // Request OTP
      cy.get('[data-testid="otp-request-button"]')
        .should("not.be.disabled")
        .click();
      cy.wait("@postRequestOtp");

      // Step 2: Should show OTP verification form
      cy.get('[data-testid="otp-verification-form"]').should("be.visible");
      cy.get('[data-testid="otp-input"]').should("be.visible");
      cy.get('[data-testid="otp-verify-button"]').should("be.disabled");

      // Enter OTP
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]')
        .should("not.be.disabled")
        .click();
      cy.wait("@postVerifyOtp");

      // Step 3: Should show tasks interface
      cy.wait("@getExternalTasks");
      cy.get('[data-testid="external-task-layout"]').should("be.visible");
      cy.get('[data-testid="external-task-header"]').should(
        "contain",
        "My Tasks",
      );
      cy.get('[data-testid="external-user-info"]').should(
        "contain",
        "John Doe",
      );
      cy.get('[data-testid="external-logout-button"]').should("be.visible");
    });

    it("should handle logout correctly", () => {
      // Complete authentication first
      cy.visit("/manual-tasks-external?token=test_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@postRequestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@postVerifyOtp");
      cy.wait("@getExternalTasks");

      // Verify logged in state
      cy.get('[data-testid="external-task-layout"]').should("be.visible");

      // Logout
      cy.get('[data-testid="external-logout-button"]').click();

      // Wait for logout to process
      cy.url().should("include", "/manual-tasks-external");
      cy.get('[data-testid="external-auth-container"]').should("be.visible");
      cy.get('[data-testid="otp-request-form"]').should("be.visible");
    });
  });

  describe("Task Management", () => {
    beforeEach(() => {
      // Helper to authenticate first
      cy.visit("/manual-tasks-external?token=test_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@postRequestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@postVerifyOtp");
      cy.wait("@getExternalTasks");
    });

    it("should display tasks table correctly", () => {
      cy.get('[data-testid="external-tasks-table"]').should("be.visible");

      // Check table headers (no "Assigned to" column for external users)
      cy.get('[data-testid="external-tasks-table"] thead th')
        .should("contain", "Task name")
        .and("contain", "Status")
        .and("contain", "System")
        .and("contain", "Type")
        .and("contain", "Days left")
        .and("contain", "Subject identity")
        .and("contain", "Actions");

      // Verify no assignee column (always filtered to current user)
      cy.get('[data-testid="external-tasks-table"] thead th').should(
        "not.contain",
        "Assigned to",
      );

      // Check first task details
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get("td")
            .eq(0)
            .should("contain", "Export Customer Data from Salesforce");
          cy.get('[data-testid="external-task-status-tag"]').should(
            "contain",
            "New",
          );
          cy.get("td").eq(2).should("contain", "Salesforce");
          cy.get("td").eq(3).should("contain", "Access");
          cy.get("td").eq(4).should("contain", "15 days");
          cy.get("td").eq(5).should("contain", "customer@example.com");
        });
    });

    it("should handle search functionality", () => {
      cy.get('[data-testid="external-tasks-search"]').type("Salesforce");
      // Should show filtered results
      cy.get('[data-testid="external-tasks-table"] tbody tr').should(
        "have.length.gte",
        1,
      );

      // Test empty search
      cy.get('[data-testid="external-tasks-search"]')
        .clear()
        .type("nonexistent");
      // Should show empty state (mocked response would handle this)
    });

    it("should show correct actions based on task status", () => {
      // Load mixed status tasks to test action visibility
      cy.intercept("GET", `${API_URL}/manual-tasks*`, {
        fixture: "external-manual-tasks/mixed-status-tasks.json",
      }).as("getMixedTasks");
      cy.reload();
      cy.wait("@getMixedTasks");

      // New task should have actions
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("New")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').should("be.visible");
          cy.get('[data-testid="task-actions-dropdown"]').should("be.visible");
        });

      // Completed task should not have actions
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Completed")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').should("not.exist");
          cy.get('[data-testid="task-actions-dropdown"]').should("not.exist");
        });

      // Skipped task should not have actions
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Skipped")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').should("not.exist");
          cy.get('[data-testid="task-actions-dropdown"]').should("not.exist");
        });
    });
  });

  describe("Complete Task Modal", () => {
    beforeEach(() => {
      // Authenticate and get to tasks
      cy.visit("/manual-tasks-external?token=test_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@postRequestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@postVerifyOtp");
      cy.wait("@getExternalTasks");
    });

    it("should handle file upload tasks", () => {
      // Find file upload task (Export Customer Data)
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Export Customer Data from Salesforce")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').should("be.visible");
      cy.get('[data-testid="complete-task-modal"]').within(() => {
        cy.contains("Complete Task").should("be.visible");
        cy.get('[data-testid="task-details-name"]').should(
          "contain",
          "Export Customer Data from Salesforce",
        );

        // Should show file upload UI - matching admin-ui test pattern
        cy.contains("Upload File").should("be.visible");
        cy.get('[data-testid="complete-modal-upload-button"]').should(
          "be.visible",
        );
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Add comment like admin-ui test (file upload requires actual file to enable save)
        cy.get('[data-testid="complete-modal-comment-input"]').type(
          "Test comment for file upload",
        );
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Cancel like admin-ui test
        cy.get('[data-testid="complete-modal-cancel-button"]').click();
      });

      cy.get('[data-testid="complete-task-modal"]').should("not.exist");
    });

    it("should handle string input tasks with validation", () => {
      // Find string input task (Export Analytics Data)
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Export Analytics Data")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        // Should show text input
        cy.get('[data-testid="complete-modal-text-input"]').should(
          "be.visible",
        );
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Test validation - empty should be disabled
        cy.get('[data-testid="complete-modal-text-input"]').type("   ");
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Valid input should enable save
        cy.get('[data-testid="complete-modal-text-input"]')
          .clear()
          .type("Analytics data exported successfully");
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "not.be.disabled",
        );

        // Add comment and submit
        cy.get('[data-testid="complete-modal-comment-input"]').type(
          "Task completed successfully",
        );
        cy.get('[data-testid="complete-modal-save-button"]').click();
      });

      cy.wait("@completeExternalTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          text_value: "Analytics data exported successfully",
          comment: "Task completed successfully",
        });
      });

      cy.get('[data-testid="complete-task-modal"]').should("not.exist");
    });

    it("should handle checkbox input tasks", () => {
      // Find checkbox task (Delete User Profile)
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Delete User Profile from MongoDB")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        // Should show checkbox (check the container, not the hidden input)
        cy.get('[data-testid="complete-modal-checkbox"]').should("exist");
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Check the checkbox (click the label area, not the hidden input)
        cy.get('[data-testid="complete-modal-checkbox"]').click();
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "not.be.disabled",
        );

        // Add comment
        cy.get('[data-testid="complete-modal-comment-input"]').type(
          "User profile deleted successfully",
        );
        cy.get('[data-testid="complete-modal-save-button"]').click();
      });

      cy.wait("@completeExternalTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          checkbox_value: true,
          comment: "User profile deleted successfully",
        });
      });

      cy.get('[data-testid="complete-task-modal"]').should("not.exist");
    });
  });

  describe("Skip Task Modal", () => {
    beforeEach(() => {
      // Authenticate and get to tasks
      cy.visit("/manual-tasks-external?token=test_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@postRequestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@postVerifyOtp");
      cy.wait("@getExternalTasks");
    });

    it("should open skip modal from dropdown and require comment", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-actions-dropdown"]').click();
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.get('[data-testid="skip-task-modal"]').should("be.visible");
      cy.get('[data-testid="skip-task-modal"]').within(() => {
        cy.contains("Skip Task").should("be.visible");
        cy.get('[data-testid="task-details-name"]').should(
          "contain",
          "Export Customer Data from Salesforce",
        );

        // Skip button should be disabled initially
        cy.get('[data-testid="skip-modal-skip-button"]').should("be.disabled");

        // Empty/whitespace should keep button disabled
        cy.get('[data-testid="skip-modal-comment-input"]').type("   ");
        cy.get('[data-testid="skip-modal-skip-button"]').should("be.disabled");

        // Valid comment should enable button
        cy.get('[data-testid="skip-modal-comment-input"]')
          .clear()
          .type("Customer withdrew request");
        cy.get('[data-testid="skip-modal-skip-button"]').should(
          "not.be.disabled",
        );

        // Verify danger styling
        cy.get('[data-testid="skip-modal-skip-button"]').should(
          "have.class",
          "ant-btn-dangerous",
        );

        // Submit
        cy.get('[data-testid="skip-modal-skip-button"]').click();
      });

      cy.wait("@skipExternalTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          comment: "Customer withdrew request",
        });
      });

      cy.get('[data-testid="skip-task-modal"]').should("not.exist");
    });

    it("should handle modal cancellation", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-actions-dropdown"]').click();
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.get('[data-testid="skip-task-modal"]').within(() => {
        // Fill comment
        cy.get('[data-testid="skip-modal-comment-input"]').type("Test reason");

        // Cancel
        cy.get('[data-testid="skip-modal-cancel-button"]').click();
      });

      cy.get('[data-testid="skip-task-modal"]').should("not.exist");

      // Reopen - field should be reset
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-actions-dropdown"]').click();
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.get('[data-testid="skip-task-modal"]').within(() => {
        cy.get('[data-testid="skip-modal-comment-input"]').should(
          "have.value",
          "",
        );
        cy.get('[data-testid="skip-modal-skip-button"]').should("be.disabled");
      });
    });
  });
});
