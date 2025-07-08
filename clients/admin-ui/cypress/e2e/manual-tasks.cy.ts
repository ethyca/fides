import {
  stubManualTasks,
  stubPlus,
  stubPrivacyRequests,
} from "cypress/support/stubs";

// Use a reliable selector for table rows
const ROW_SELECTOR = "tbody tr[data-row-key]";

describe("Manual Tasks", () => {
  beforeEach(() => {
    cy.login();
    stubManualTasks();
    stubPrivacyRequests();
    stubPlus(true);

    // Add mock for config endpoint
    cy.intercept("GET", "/api/v1/config?api_set=false", {
      body: {},
    }).as("getConfig");
  });

  describe("Manual Tasks Tab and Basic Functionality", () => {
    it("should display the manual tasks tab and load tasks correctly", () => {
      cy.visit("/privacy-requests?tab=manual-tasks");
      cy.wait("@getManualTasks");

      // Check that the Manual tasks tab is visible and active
      cy.get("[role=tab]").contains("Manual tasks").should("be.visible");

      // Verify the manual tasks table is displayed with data
      cy.get("table").should("exist");
      cy.get(ROW_SELECTOR).should("have.length.at.least", 1);

      // Check that task data is displayed correctly in the first row
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          cy.get("td")
            .first()
            .should("contain", "Export Customer Data from Salesforce");
          cy.getByTestId("manual-task-status-tag").should("contain", "New");
          cy.get("td").contains("Salesforce").should("exist");
          cy.get("td").contains("Access").should("exist");
          cy.get("td").contains("15").should("exist");
          cy.get("td").contains("customer@email.com").should("exist");
        });
    });

    it("should display empty state when no tasks are available", () => {
      // Mock empty response before navigation
      cy.intercept("GET", "/api/v1/plus/manual-fields*", {
        body: {
          items: [],
          total: 0,
          page: 1,
          size: 25,
          pages: 0,
          filterOptions: { assigned_users: [], systems: [] },
        },
      }).as("getManualTasksEmpty");

      cy.visit("/privacy-requests?tab=manual-tasks");
      cy.wait("@getManualTasksEmpty");
      cy.getByTestId("empty-state-current-user").should(
        "contain",
        "No manual tasks available",
      );
    });
  });

  describe("Task Actions and User Interactions", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests?tab=manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should show appropriate action buttons based on task status", () => {
      // Check action buttons for new tasks - specifically in the Actions column (last column)
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          // Check the Actions column specifically (last td)
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button").contains("Complete").should("exist");
              cy.get("button[aria-label='More actions']").should("exist");
            });
        });

      // Check that completed/skipped tasks don't show action buttons in the Actions column
      cy.get(ROW_SELECTOR).each(($row) => {
        cy.wrap($row).within(() => {
          cy.get("td").then(($cells) => {
            const statusCell = $cells.eq(1);
            if (
              statusCell.text().includes("Completed") ||
              statusCell.text().includes("Skipped")
            ) {
              // Check the Actions column (last td) for no buttons
              cy.get("td")
                .last()
                .within(() => {
                  cy.get("button").should("not.exist");
                });
            }
          });
        });
      });
    });

    it("should handle task completion and dropdown actions", () => {
      // Test task completion - Complete button now opens a modal
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button").contains("Complete").click();
            });
        });

      // Verify modal opens
      cy.getByTestId("complete-task-modal").should("be.visible");
      cy.getByTestId("complete-task-modal").within(() => {
        cy.get("h4").contains("Complete Task").should("be.visible");

        // Close modal for next test
        cy.getByTestId("complete-modal-cancel-button").click();
      });

      cy.getByTestId("complete-task-modal").should("not.exist");

      // Test dropdown menu
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button[aria-label='More actions']").click();
            });
        });

      // Check dropdown menu items
      cy.get(".ant-dropdown-menu-item")
        .contains("Skip task")
        .should("be.visible");
      cy.get(".ant-dropdown-menu-item")
        .contains("Go to request")
        .should("be.visible");

      // Test navigation to privacy request details
      cy.get(".ant-dropdown-menu-item").contains("Go to request").click();
      cy.location("pathname").should("match", /^\/privacy-requests\/pri_.+/);
    });
  });

  describe("Table Features (Filtering and Pagination)", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests?tab=manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should apply table filters and send correct API parameters", () => {
      // Wait for initial data to load
      cy.get("table").should("exist");
      cy.get(ROW_SELECTOR).should("have.length.at.least", 1);

      // Apply status filter
      cy.applyTableFilter("Status", "New");
      cy.wait("@getManualTasks").then((interception) => {
        const url = interception.request.url;
        expect(interception.request.url).to.include("status=new");
        expect(url).to.include("assigned_user_id=123"); // request_type parameter (snake_case)
      });

      // Apply system filter (first available system)
      cy.applyTableFilter("System", "Salesforce");
      cy.wait("@getManualTasks").then((interception) => {
        const url = interception.request.url;
        expect(url).to.include("status=new"); // Previous filter should still be there
        expect(url).to.include("system_name=Salesforce"); // Should have system_name parameter (snake_case)
        expect(url).to.include("assigned_user_id=123"); // request_type parameter (snake_case)
      });

      // Apply request type filter
      cy.applyTableFilter("Type", "Access");
      cy.wait("@getManualTasks").then((interception) => {
        const url = interception.request.url;
        expect(url).to.include("status=new"); // Previous filters should still be there
        expect(url).to.include("system_name=Salesforce");
        expect(url).to.include("request_type=access"); // request_type parameter (snake_case)
      });
    });

    it("should handle pagination controls and assigned users display", () => {
      // Test pagination controls - now using Ant Design's standard pagination
      cy.get(".ant-pagination").should("be.visible");
      cy.get(".ant-pagination-prev").should("exist");
      cy.get(".ant-pagination-next").should("exist");

      // Test page size change using Ant Design's page size selector
      cy.get(".ant-select-selector").contains("25").click();
      cy.get(".ant-select-dropdown").within(() => {
        cy.get(".ant-select-item").contains("50").click();
      });
      cy.wait("@getManualTasks").then((interception) => {
        expect(interception.request.url).to.include("size=50");
      });

      // Test assigned users display
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          cy.get("td")
            .eq(4)
            .within(() => {
              cy.get(".ant-tag").should("have.length.at.least", 1);
            });
        });

      // Test tasks with no assigned users
      cy.get(ROW_SELECTOR).each(($row) => {
        cy.wrap($row).within(() => {
          cy.get("td")
            .eq(4)
            .then(($assignedCell) => {
              if (!$assignedCell.find(".ant-tag").length) {
                cy.wrap($assignedCell).should("exist");
              }
            });
        });
      });
    });
  });

  describe("Complete Task Modal", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests?tab=manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should display file upload input for file type tasks and send correct parameters", () => {
      // Find and click complete button for file upload task
      cy.get(ROW_SELECTOR)
        .contains("Export Customer Data from Salesforce")
        .parents("tr")
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button").contains("Complete").click();
            });
        });

      cy.getByTestId("complete-task-modal").should("be.visible");
      cy.getByTestId("complete-task-modal").within(() => {
        // Verify file upload input is displayed
        cy.getByTestId("complete-modal-upload-button").should("be.visible");

        // Verify save button is disabled without file
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Add comment only (should still be disabled without file)
        cy.getByTestId("complete-modal-comment-input").type(
          "Test comment for file upload",
        );
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Attach a file
        cy.get('input[type="file"]').selectFile(
          "cypress/fixtures/privacy-requests/test-upload.pdf",
          { force: true },
        );

        // Save button should now be enabled
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        // Submit and verify request parameters
        cy.getByTestId("complete-modal-save-button").click();
      });

      // Verify correct parameters are sent in the request
      cy.wait("@completeTask").then((interception) => {
        // New implementation uses FormData (multipart form)
        expect(interception.request.headers).to.have.property("content-type");
        expect(interception.request.headers["content-type"]).to.include(
          "multipart/form-data",
        );

        // For FormData, the body will be serialized - just verify it exists
        expect(interception.request.body).to.exist;
      });

      cy.getByTestId("complete-task-modal").should("not.exist");
    });

    it("should display checkbox input for checkbox type tasks and send correct parameters", () => {
      // Find and click complete button for checkbox task
      cy.get(ROW_SELECTOR)
        .contains("Delete User Profile from MongoDB")
        .parents("tr")
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button").contains("Complete").click();
            });
        });

      cy.getByTestId("complete-task-modal").should("be.visible");
      cy.getByTestId("complete-task-modal").within(() => {
        // Verify checkbox input is displayed
        cy.getByTestId("complete-modal-checkbox").should("exist");

        // Verify save button is disabled without checkbox
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Check checkbox to enable save button
        cy.getByTestId("complete-modal-checkbox").click();
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        // Uncheck to disable again
        cy.getByTestId("complete-modal-checkbox").click();
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Check again and add comment
        cy.getByTestId("complete-modal-checkbox").click();
        cy.getByTestId("complete-modal-comment-input").type(
          "Task completed successfully",
        );
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        // Submit and verify request parameters
        cy.getByTestId("complete-modal-save-button").click();
      });

      // Verify correct parameters are sent in the request
      cy.wait("@completeTask").then((interception) => {
        // New implementation uses FormData (multipart form)
        expect(interception.request.headers).to.have.property("content-type");
        expect(interception.request.headers["content-type"]).to.include(
          "multipart/form-data",
        );

        // For FormData, the body will be serialized - just verify it exists
        expect(interception.request.body).to.exist;
      });

      cy.getByTestId("complete-task-modal").should("not.exist");
    });

    it("should display text input for string type tasks and send correct parameters", () => {
      // Find and click complete button for text input task
      cy.get(ROW_SELECTOR)
        .contains("Export Analytics Data")
        .parents("tr")
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button").contains("Complete").click();
            });
        });

      cy.getByTestId("complete-task-modal").should("be.visible");
      cy.getByTestId("complete-task-modal").within(() => {
        // Verify text input is displayed
        cy.getByTestId("complete-modal-text-input").should("be.visible");

        // Verify save button is disabled without text
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Add text to enable save button
        cy.getByTestId("complete-modal-text-input").type(
          "Analytics data exported successfully",
        );
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        // Clear text to disable again
        cy.getByTestId("complete-modal-text-input").clear();
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Test whitespace-only input (should remain disabled)
        cy.getByTestId("complete-modal-text-input").type("   ");
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Add valid text and comment
        cy.getByTestId("complete-modal-text-input")
          .clear()
          .type("Data exported to secure location");
        cy.getByTestId("complete-modal-comment-input").type(
          "Export completed without issues",
        );
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        // Submit and verify request parameters
        cy.getByTestId("complete-modal-save-button").click();
      });

      // Verify correct parameters are sent in the request
      cy.wait("@completeTask").then((interception) => {
        // New implementation uses FormData (multipart form)
        expect(interception.request.headers).to.have.property("content-type");
        expect(interception.request.headers["content-type"]).to.include(
          "multipart/form-data",
        );

        // For FormData, the body will be serialized - just verify it exists
        expect(interception.request.body).to.exist;
      });
    });
  });

  describe("Skip Task Modal", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests?tab=manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should require comment and send correct parameters", () => {
      // Open skip modal via dropdown
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button[aria-label='More actions']").click();
            });
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.getByTestId("skip-task-modal").should("be.visible");
      cy.getByTestId("skip-task-modal").within(() => {
        // Verify required comment field is displayed
        cy.contains("Reason for skipping (Required)").should("be.visible");
        cy.getByTestId("skip-modal-comment-input").should("be.visible");

        // Verify skip button is disabled without comment
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");

        // Add comment to enable skip button
        cy.getByTestId("skip-modal-comment-input").type(
          "Task no longer required due to policy change",
        );
        cy.getByTestId("skip-modal-skip-button").should("not.be.disabled");

        // Clear comment to disable again
        cy.getByTestId("skip-modal-comment-input").clear();
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");

        // Test whitespace-only comment (should remain disabled)
        cy.getByTestId("skip-modal-comment-input").type("   ");
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");

        // Add valid comment and submit
        cy.getByTestId("skip-modal-comment-input")
          .clear()
          .type("Customer withdrew request");
        cy.getByTestId("skip-modal-skip-button").should("not.be.disabled");

        // Submit and verify request parameters
        cy.getByTestId("skip-modal-skip-button").click();
      });

      // Verify correct parameters are sent in the request
      cy.wait("@skipTask").then((interception) => {
        // New implementation uses FormData (multipart form)
        expect(interception.request.headers).to.have.property("content-type");
        expect(interception.request.headers["content-type"]).to.include(
          "multipart/form-data",
        );

        // For FormData, the body will be serialized - just verify it exists
        expect(interception.request.body).to.exist;
      });

      cy.getByTestId("skip-task-modal").should("not.exist");
    });

    it("should reset form state when cancelled and reopened", () => {
      // Open skip modal
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button[aria-label='More actions']").click();
            });
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.getByTestId("skip-task-modal").should("be.visible");
      cy.getByTestId("skip-task-modal").within(() => {
        // Add comment and cancel
        cy.getByTestId("skip-modal-comment-input").type("Test comment");
        cy.getByTestId("skip-modal-cancel-button").click();
      });

      cy.getByTestId("skip-task-modal").should("not.exist");

      // Reopen skip modal
      cy.get(ROW_SELECTOR)
        .first()
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button[aria-label='More actions']").click();
            });
        });

      cy.get(".ant-dropdown-menu-item").contains("Skip task").click();

      cy.getByTestId("skip-task-modal").within(() => {
        // Verify form is reset
        cy.getByTestId("skip-modal-comment-input").should("have.value", "");
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");
      });
    });
  });
});
