import { stubManualTasks, stubPlus } from "cypress/support/stubs";

describe("Manual Tasks", () => {
  beforeEach(() => {
    cy.login();
    stubManualTasks();
    stubPlus(true);
  });

  describe("Manual Tasks Tab and Basic Functionality", () => {
    it("should display the manual tasks tab and load tasks correctly", () => {
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");

      // Check that the Manual tasks tab is visible and active
      cy.get("[role=tab]").contains("Manual tasks").should("be.visible");

      // Verify the manual tasks table is displayed with data
      cy.get("table").should("exist");
      cy.get("tbody tr").should("have.length.at.least", 1);

      // Check that task data is displayed correctly in the first row
      cy.get("tbody tr")
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

    it("should handle search functionality and empty states", () => {
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");

      // Test search functionality
      cy.get("input[placeholder*='Search by name or description']").type(
        "Salesforce",
      );
      cy.wait("@getManualTasks");

      // Test empty state for search with no results
      cy.intercept("GET", "/api/v1/manual-tasks*", {
        body: {
          items: [],
          total: 0,
          page: 1,
          size: 25,
          pages: 0,
          filterOptions: { assigned_users: [], systems: [] },
        },
      }).as("getEmptySearchTasks");

      cy.get("input[placeholder*='Search by name or description']")
        .clear()
        .type("nonexistent");
      cy.wait("@getEmptySearchTasks");
      cy.get("table").should("contain", "No tasks match your search");
    });

    it("should display empty state when no tasks are available", () => {
      // Mock empty response before navigation
      cy.intercept("GET", "/api/v1/manual-tasks?page=1&size=25&search=*", {
        body: {
          items: [],
          total: 0,
          page: 1,
          size: 25,
          pages: 0,
          filterOptions: { assigned_users: [], systems: [] },
        },
      }).as("getManualTasksEmpty");

      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasksEmpty");
      cy.getByTestId("empty-state").should(
        "contain",
        "No manual tasks available",
      );
    });
  });

  describe("Task Actions and User Interactions", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should show appropriate action buttons based on task status", () => {
      // Check action buttons for new tasks - specifically in the Actions column (last column)
      cy.get("tbody tr")
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
      cy.get("tbody tr").each(($row) => {
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
      cy.get("tbody tr")
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
      cy.get("tbody tr")
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
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should apply table filters and send correct API parameters", () => {
      // Wait for initial data to load
      cy.get("table").should("exist");
      cy.get("tbody tr").should("have.length.at.least", 1);

      // Apply status filter
      cy.applyTableFilter("Status", "New");
      cy.wait("@getManualTasks").then((interception) => {
        expect(interception.request.url).to.include("status=new");
      });

      // Apply system filter (first available system)
      cy.applyTableFilter("System", "Salesforce");
      cy.wait("@getManualTasks").then((interception) => {
        const url = interception.request.url;
        expect(url).to.include("status=new"); // Previous filter should still be there
        expect(url).to.include("systemName=Salesforce"); // Should have systemName parameter (camelCase)
      });

      // Apply request type filter
      cy.applyTableFilter("Type", "Access");
      cy.wait("@getManualTasks").then((interception) => {
        const url = interception.request.url;
        expect(url).to.include("status=new"); // Previous filters should still be there
        expect(url).to.include("systemName=Salesforce");
        expect(url).to.include("requestType=access"); // requestType parameter (camelCase)
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
      cy.get("tbody tr")
        .first()
        .within(() => {
          cy.get("td")
            .eq(4)
            .within(() => {
              cy.get(".ant-tag").should("have.length.at.least", 1);
            });
        });

      // Test tasks with no assigned users
      cy.get("tbody tr").each(($row) => {
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
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should display file upload input for file type tasks and validate correctly", () => {
      cy.get("tbody tr")
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
        cy.contains("Upload File").should("be.visible");
        cy.getByTestId("complete-modal-upload-button").should("be.visible");
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        // Verify improved TaskDetails: proper request type mapping and ant tags
        cy.contains("Request Type").should("be.visible");
        cy.getByTestId("assigned-users-tags").should("exist"); // Ant tags for assigned users
        cy.getByTestId("assigned-users-tags").within(() => {
          cy.get("[data-testid^='assigned-user-tag-']").should(
            "have.length.at.least",
            1,
          );
        });
        cy.contains("Identity -").should("exist"); // Multiple identity fields

        cy.getByTestId("complete-modal-comment-input").type(
          "Test comment for file upload",
        );
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        cy.getByTestId("complete-modal-cancel-button").click();
      });

      cy.getByTestId("complete-task-modal").should("not.exist");
    });

    it("should display checkbox input for checkbox type tasks and validate correctly", () => {
      cy.get("tbody tr")
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
        cy.getByTestId("complete-modal-checkbox").should("exist");
        cy.contains("The task has been completed").should("be.visible");
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        cy.getByTestId("complete-modal-checkbox").click();
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        cy.getByTestId("complete-modal-checkbox").click();
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        cy.getByTestId("complete-modal-checkbox").click();
        cy.getByTestId("complete-modal-comment-input").type(
          "Task completed successfully",
        );
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        cy.getByTestId("complete-modal-save-button").click();
      });

      cy.wait("@completeTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          task_id: "task_002",
          checkbox_value: true,
          comment: "Task completed successfully",
        });
        expect(interception.request.body).to.not.have.property("text_value");
        expect(interception.request.body).to.not.have.property(
          "attachment_type",
        );
      });

      cy.getByTestId("complete-task-modal").should("not.exist");
    });

    it("should display text input for string type tasks and validate correctly", () => {
      cy.get("tbody tr")
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
        cy.contains("Text Input").should("be.visible");
        cy.getByTestId("complete-modal-text-input").should("be.visible");
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        cy.getByTestId("complete-modal-text-input").type(
          "Analytics data exported successfully",
        );
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        cy.getByTestId("complete-modal-text-input").clear();
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        cy.getByTestId("complete-modal-text-input").type("   ");
        cy.getByTestId("complete-modal-save-button").should("be.disabled");

        cy.getByTestId("complete-modal-text-input")
          .clear()
          .type("Data exported to secure location");
        cy.getByTestId("complete-modal-comment-input").type(
          "Export completed without issues",
        );
        cy.getByTestId("complete-modal-save-button").should("not.be.disabled");

        cy.getByTestId("complete-modal-save-button").click();
      });

      cy.wait("@completeTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          task_id: "task_004",
          text_value: "Data exported to secure location",
          comment: "Export completed without issues",
        });
        expect(interception.request.body).to.not.have.property(
          "checkbox_value",
        );
        expect(interception.request.body).to.not.have.property(
          "attachment_type",
        );
      });

      cy.getByTestId("complete-task-modal").should("not.exist");
    });

    it("should allow skipping task from complete modal", () => {
      cy.get("tbody tr")
        .first()
        .within(() => {
          cy.get("td")
            .last()
            .within(() => {
              cy.get("button").contains("Complete").click();
            });
        });

      cy.getByTestId("complete-task-modal").should("be.visible");
      cy.getByTestId("complete-task-modal").within(() => {
        cy.getByTestId("complete-modal-skip-button").click();
      });

      cy.getByTestId("skip-task-modal").should("be.visible");
    });
  });

  describe("Skip Task Modal", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");
    });

    it("should display skip modal with required comment field and validate correctly", () => {
      cy.get("tbody tr")
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
        cy.contains("Reason for skipping (Required)").should("be.visible");
        cy.getByTestId("skip-modal-comment-input").should("be.visible");
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");

        cy.getByTestId("skip-modal-comment-input").type(
          "Task no longer required due to policy change",
        );
        cy.getByTestId("skip-modal-skip-button").should("not.be.disabled");

        cy.getByTestId("skip-modal-comment-input").clear();
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");

        cy.getByTestId("skip-modal-comment-input").type("   ");
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");

        cy.getByTestId("skip-modal-comment-input")
          .clear()
          .type("Customer withdrew request");
        cy.getByTestId("skip-modal-skip-button").should("not.be.disabled");

        cy.getByTestId("skip-modal-skip-button").click();
      });

      cy.wait("@skipTask").then((interception) => {
        expect(interception.request.body).to.deep.include({
          task_id: "task_001",
          comment: "Customer withdrew request",
        });
      });

      cy.getByTestId("skip-task-modal").should("not.exist");
    });

    it("should handle cancel button correctly", () => {
      cy.get("tbody tr")
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
        cy.getByTestId("skip-modal-comment-input").type("Test comment");
        cy.getByTestId("skip-modal-cancel-button").click();
      });

      cy.getByTestId("skip-task-modal").should("not.exist");

      cy.get("tbody tr")
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
        cy.getByTestId("skip-modal-comment-input").should("have.value", "");
        cy.getByTestId("skip-modal-skip-button").should("be.disabled");
      });
    });

    it("should show danger styling on Skip Task button", () => {
      cy.get("tbody tr")
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
        cy.getByTestId("skip-modal-comment-input").type("Test reason");
        cy.getByTestId("skip-modal-skip-button").should(
          "have.class",
          "ant-btn-dangerous",
        );
      });
    });
  });
});
