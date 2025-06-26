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
      // Test task completion
      cy.get("tbody tr")
        .first()
        .within(() => {
          cy.get("button").contains("Complete").click();
        });
      cy.wait("@completeTask").then((interception) => {
        expect(interception.request.body).to.have.property("task_id");
      });

      // Reset and test dropdown menu
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");

      cy.get("tbody tr")
        .first()
        .within(() => {
          cy.get("button[aria-label='More actions']").click();
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
});
