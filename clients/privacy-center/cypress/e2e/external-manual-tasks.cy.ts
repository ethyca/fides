describe("External Manual Tasks", () => {
  beforeEach(() => {
    // Setup API interceptors for real endpoint testing
    cy.intercept("POST", "/api/v1/external-login/request-otp", {
      fixture: "external-manual-tasks/auth-responses.json",
    }).as("requestOtp");

    cy.intercept("POST", "/api/v1/external-login/verify-otp", {
      fixture: "external-manual-tasks/auth-responses.json",
    }).as("verifyOtp");

    cy.intercept("GET", "/api/v1/manual-tasks*", {
      fixture: "external-manual-tasks/user-tasks.json",
    }).as("getUserTasks");

    cy.intercept("POST", "/api/v1/manual-tasks/*/complete", {
      fixture: "external-manual-tasks/complete-task-success.json",
    }).as("completeTask");

    cy.intercept("POST", "/api/v1/manual-tasks/*/skip", {
      fixture: "external-manual-tasks/skip-task-success.json",
    }).as("skipTask");
  });

  describe("Authentication Flow", () => {
    it("should complete full OTP authentication flow", () => {
      cy.visit("/manual-tasks-external?token=valid_token_123");

      // Step 1: Should show OTP request form
      cy.get('[data-testid="external-auth-container"]').should("be.visible");
      cy.get('[data-testid="otp-request-form"]').should("be.visible");
      cy.get('[data-testid="otp-request-email-display"]').should(
        "contain",
        "user@example.com",
      );

      // Request OTP
      cy.get('[data-testid="otp-request-button"]').should("not.be.disabled");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");

      // Step 2: Should show OTP verification form
      cy.get('[data-testid="otp-verification-form"]').should("be.visible");
      cy.get('[data-testid="otp-input"]').should("be.visible");
      cy.get('[data-testid="otp-verify-button"]').should("be.disabled");

      // Enter OTP
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').should("not.be.disabled");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");

      // Step 3: Should show tasks interface
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

    // it("should handle invalid email token", () => {
      cy.visit("/manual-tasks-external?token=invalid_token");

      cy.intercept("POST", "/api/v1/external-login/request-otp", {
        statusCode: 401,
        body: {
          detail: "Email token expired. Please use a link from a recent email.",
        },
      }).as("invalidToken");

      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@invalidToken");

      cy.get('[data-testid="auth-error-message"]')
        .should("be.visible")
        .and("contain", "Email token expired");
    });

    it("should handle invalid OTP code", () => {
      cy.visit("/manual-tasks-external?token=valid_token_123");

      // Complete OTP request
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");

      // Enter invalid OTP
      cy.intercept("POST", "/api/v1/external-login/verify-otp", {
        statusCode: 401,
        body: { detail: "Invalid OTP code" },
      }).as("invalidOtp");

      cy.get('[data-testid="otp-input"]').type("wrong-code");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@invalidOtp");

      cy.get('[data-testid="auth-error-message"]')
        .should("be.visible")
        .and("contain", "Invalid OTP code");
    });

    it("should handle logout correctly", () => {
      // Complete authentication first
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");

      // Verify logged in state
      cy.get('[data-testid="external-task-layout"]').should("be.visible");

      // Logout
      cy.get('[data-testid="external-logout-button"]').click();
      cy.get('[data-testid="external-auth-container"]').should("be.visible");
      cy.get('[data-testid="otp-request-form"]').should("be.visible");
    });
  });

  describe("Tasks Interface", () => {
    beforeEach(() => {
      // Helper to authenticate first
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getUserTasks");
    });

    it("should display tasks table with correct columns", () => {
      cy.get('[data-testid="external-tasks-table"]').should("be.visible");

      // Check table headers - external users don't see "Assigned to" column
      cy.get('[data-testid="external-tasks-table"] thead th')
        .should("contain", "Task name")
        .and("contain", "Status")
        .and("contain", "System")
        .and("contain", "Type")
        .and("contain", "Days left")
        .and("contain", "Subject identity")
        .and("contain", "Actions")
        .and("not.contain", "Assigned to");
    });

    it("should show task details correctly", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get("td").eq(0).should("contain", "Export Customer Data");
          cy.get('[data-testid="external-task-status-tag"]').should(
            "contain",
            "New",
          );
          cy.get("td").eq(2).should("contain", "Salesforce");
          cy.get("td").eq(3).should("contain", "Access");
          cy.get("td").eq(4).should("contain", "15");
          cy.get("td").eq(5).should("contain", "customer@example.com");
        });
    });

    it("should handle search functionality", () => {
      cy.get('[data-testid="external-tasks-search"]').type("Salesforce");

      // Should filter results (mocked response handles this)
      cy.get('[data-testid="external-tasks-table"] tbody tr').should(
        "have.length.gte",
        1,
      );

      cy.get('[data-testid="external-tasks-search"]')
        .clear()
        .type("nonexistent");
      cy.get('[data-testid="external-empty-state"]')
        .should("be.visible")
        .and("contain", "No tasks match your search");
    });

    it("should handle status filter", () => {
      // Click status filter dropdown
      cy.get('[data-testid="external-tasks-table"] thead th')
        .contains("Status")
        .find(".ant-table-filter-trigger")
        .click();

      // Select "Completed" filter
      cy.get(".ant-dropdown-menu .ant-checkbox-wrapper")
        .contains("Completed")
        .click();

      cy.get(".ant-btn-primary").click(); // Apply filter

      // Verify filtered results
      cy.get('[data-testid="external-task-status-tag"]').should(
        "contain",
        "Completed",
      );
    });

    it("should show empty state when no tasks", () => {
      // Mock empty response
      cy.intercept("GET", "/api/v1/manual-tasks*", {
        body: {
          items: [],
          total: 0,
          page: 1,
          size: 25,
          pages: 0,
        },
      }).as("getEmptyTasks");

      cy.reload();
      cy.wait("@getEmptyTasks");

      cy.get('[data-testid="external-empty-state"]')
        .should("be.visible")
        .and("contain", "No manual tasks available");
    });
  });

  describe("Complete Task Modal", () => {
    beforeEach(() => {
      // Authenticate and get to tasks
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getUserTasks");
    });

    it("should open complete task modal", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').should("be.visible");
      cy.get('[data-testid="complete-task-modal"]').within(() => {
        cy.contains("Complete Task").should("be.visible");
        cy.get('[data-testid="task-details-name"]').should(
          "contain",
          "Export Customer Data",
        );
      });
    });

    it("should handle string input type tasks", () => {
      // Find a string input task
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Analytics Data")
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

        // Fill required field
        cy.get('[data-testid="complete-modal-text-input"]').type(
          "Data exported successfully",
        );
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "not.be.disabled",
        );

        // Add optional comment
        cy.get('[data-testid="complete-modal-comment-input"]').type(
          "Task completed without issues",
        );

        // Submit
        cy.get('[data-testid="complete-modal-save-button"]').click();
      });

      cy.wait("@completeTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          text_value: "Data exported successfully",
          comment: "Task completed without issues",
        });
      });

      cy.get('[data-testid="complete-task-modal"]').should("not.exist");
    });

    it("should handle checkbox input type tasks", () => {
      // Find a checkbox task
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Delete User Profile")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        // Should show checkbox
        cy.get('[data-testid="complete-modal-checkbox"]').should("be.visible");
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Check the checkbox
        cy.get('[data-testid="complete-modal-checkbox"]').check();
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "not.be.disabled",
        );

        cy.get('[data-testid="complete-modal-save-button"]').click();
      });

      cy.wait("@completeTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          checkbox_value: true,
        });
      });
    });

    it("should handle file upload tasks", () => {
      // Find a file upload task
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .contains("Export Customer Data")
        .parents("tr")
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        // Should show upload component
        cy.get('[data-testid="complete-modal-file-upload"]').should(
          "be.visible",
        );
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Simulate file upload
        const fileName = "customer-data.csv";
        cy.get('[data-testid="complete-modal-upload-button"]').selectFile({
          contents: Cypress.Buffer.from("customer data content"),
          fileName,
        });

        cy.get('[data-testid="complete-modal-save-button"]').should(
          "not.be.disabled",
        );
        cy.get('[data-testid="complete-modal-save-button"]').click();
      });

      cy.wait("@completeTask").then((interception) => {
        expect(interception.request.body).to.have.property(
          "attachment_type",
          "file",
        );
      });
    });

    it("should validate required fields correctly", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        // Save button should be disabled initially
        cy.get('[data-testid="complete-modal-save-button"]').should(
          "be.disabled",
        );

        // Test validation based on task type - will vary based on input_type
        cy.get("body").then(($body) => {
          if (
            $body.find('[data-testid="complete-modal-text-input"]').length > 0
          ) {
            // String input validation
            cy.get('[data-testid="complete-modal-text-input"]').type("   ");
            cy.get('[data-testid="complete-modal-save-button"]').should(
              "be.disabled",
            );

            cy.get('[data-testid="complete-modal-text-input"]')
              .clear()
              .type("Valid input");
            cy.get('[data-testid="complete-modal-save-button"]').should(
              "not.be.disabled",
            );
          } else if (
            $body.find('[data-testid="complete-modal-checkbox"]').length > 0
          ) {
            // Checkbox validation
            cy.get('[data-testid="complete-modal-checkbox"]').check();
            cy.get('[data-testid="complete-modal-save-button"]').should(
              "not.be.disabled",
            );
          }
        });
      });
    });

    it("should handle modal cancellation", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        // Fill some data
        cy.get('[data-testid="complete-modal-comment-input"]').type(
          "Test comment",
        );

        // Cancel
        cy.get('[data-testid="complete-modal-cancel-button"]').click();
      });

      cy.get('[data-testid="complete-task-modal"]').should("not.exist");

      // Reopen modal - fields should be reset
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        cy.get('[data-testid="complete-modal-comment-input"]').should(
          "have.value",
          "",
        );
      });
    });

    it("should allow skipping from complete modal", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        cy.get('[data-testid="complete-modal-skip-button"]').click();
      });

      // Should close complete modal and open skip modal
      cy.get('[data-testid="complete-task-modal"]').should("not.exist");
      cy.get('[data-testid="skip-task-modal"]').should("be.visible");
    });
  });

  describe("Skip Task Modal", () => {
    beforeEach(() => {
      // Authenticate and get to tasks
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getUserTasks");
    });

    it("should open skip task modal from dropdown", () => {
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
          "Export Customer Data",
        );
      });
    });

    it("should require comment for skipping", () => {
      // Open skip modal
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-actions-dropdown"]').click();
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.get('[data-testid="skip-task-modal"]').within(() => {
        // Skip button should be disabled initially
        cy.get('[data-testid="skip-modal-skip-button"]').should("be.disabled");

        // Empty/whitespace should keep button disabled
        cy.get('[data-testid="skip-modal-comment-input"]').type("   ");
        cy.get('[data-testid="skip-modal-skip-button"]').should("be.disabled");

        // Valid comment should enable button
        cy.get('[data-testid="skip-modal-comment-input"]')
          .clear()
          .type("Task no longer needed");
        cy.get('[data-testid="skip-modal-skip-button"]').should(
          "not.be.disabled",
        );

        // Submit
        cy.get('[data-testid="skip-modal-skip-button"]').click();
      });

      cy.wait("@skipTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          comment: "Task no longer needed",
        });
      });

      cy.get('[data-testid="skip-task-modal"]').should("not.exist");
    });

    it("should handle modal cancellation", () => {
      // Open skip modal
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

    it("should show danger styling on skip button", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-actions-dropdown"]').click();
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.get('[data-testid="skip-task-modal"]').within(() => {
        cy.get('[data-testid="skip-modal-comment-input"]').type("Valid reason");
        cy.get('[data-testid="skip-modal-skip-button"]')
          .should("not.be.disabled")
          .and("have.class", "ant-btn-dangerous");
      });
    });
  });

  describe("Task Action Visibility", () => {
    beforeEach(() => {
      // Mock tasks with different statuses
      cy.intercept("GET", "/api/v1/manual-tasks*", {
        fixture: "external-manual-tasks/mixed-status-tasks.json",
      }).as("getMixedTasks");

      // Authenticate
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getMixedTasks");
    });

    it("should only show actions for new tasks", () => {
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

  describe("Error Handling", () => {
    it("should handle API errors gracefully", () => {
      // Mock API error
      cy.intercept("GET", "/api/v1/manual-tasks*", {
        statusCode: 500,
        body: { detail: "Internal server error" },
      }).as("getTasksError");

      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getTasksError");

      cy.get('[data-testid="tasks-error-message"]')
        .should("be.visible")
        .and("contain", "Failed to load tasks");
    });

    it("should handle task completion errors", () => {
      // Complete auth
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getUserTasks");

      // Mock completion error
      cy.intercept("POST", "/api/v1/manual-tasks/*/complete", {
        statusCode: 400,
        body: { detail: "Task cannot be completed" },
      }).as("completeTaskError");

      // Try to complete task
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      cy.get('[data-testid="complete-task-modal"]').within(() => {
        cy.get('[data-testid="complete-modal-save-button"]').click();
      });

      cy.wait("@completeTaskError");

      cy.get('[data-testid="task-completion-error"]')
        .should("be.visible")
        .and("contain", "Failed to complete task");
    });
  });

  describe("Responsive Design", () => {
    beforeEach(() => {
      // Complete auth flow
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getUserTasks");
    });

    it("should work on mobile viewport", () => {
      cy.viewport("iphone-x");

      // Table should be scrollable on mobile
      cy.get('[data-testid="external-tasks-table"]').should("be.visible");

      // User info should be visible
      cy.get('[data-testid="external-user-info"]').should("be.visible");

      // Logout button should be accessible
      cy.get('[data-testid="external-logout-button"]').should("be.visible");
    });

    it("should work on tablet viewport", () => {
      cy.viewport("ipad-2");

      cy.get('[data-testid="external-tasks-table"]').should("be.visible");
      cy.get('[data-testid="external-task-layout"]').should("be.visible");
    });
  });

  describe("Accessibility", () => {
    beforeEach(() => {
      // Complete auth flow
      cy.visit("/manual-tasks-external?token=valid_token_123");
      cy.get('[data-testid="otp-request-button"]').click();
      cy.wait("@requestOtp");
      cy.get('[data-testid="otp-input"]').type("123456");
      cy.get('[data-testid="otp-verify-button"]').click();
      cy.wait("@verifyOtp");
      cy.wait("@getUserTasks");
    });

    it("should have proper ARIA labels", () => {
      cy.get('[data-testid="task-actions-dropdown"]').should(
        "have.attr",
        "aria-label",
        "More actions",
      );
      cy.get('[data-testid="external-logout-button"]').should(
        "have.attr",
        "aria-label",
        "Logout",
      );
    });

    it("should be keyboard navigable", () => {
      // Tab through interface
      cy.get("body").tab();
      cy.focused().should("have.attr", "data-testid", "external-tasks-search");

      cy.focused().tab();
      cy.focused().should("have.attr", "data-testid", "task-complete-button");
    });

    it("should have proper focus management in modals", () => {
      cy.get('[data-testid="external-tasks-table"] tbody tr')
        .first()
        .within(() => {
          cy.get('[data-testid="task-complete-button"]').click();
        });

      // Focus should be on first input in modal
      cy.get('[data-testid="complete-task-modal"]').within(() => {
        cy.focused().should("exist");
      });
    });
  });
});
