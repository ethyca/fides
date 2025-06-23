import { stubManualTasks, stubPlus } from "cypress/support/stubs";

describe("Manual Tasks", () => {
  beforeEach(() => {
    cy.login();
    stubManualTasks();
    stubPlus(true);
  });

  describe("Manual Tasks Tab and Basic Functionality", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests#manual-tasks");
      cy.getByTestId("privacy-requests").should("exist");
    });

    it("should display the manual tasks tab and load tasks correctly", () => {
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
      cy.intercept("GET", "/api/v1/manual-tasks*", {
        body: {
          items: [],
          total: 0,
          page: 1,
          size: 25,
          pages: 0,
          filterOptions: { assigned_users: [], systems: [] },
        },
      }).as("getManualTasks");

      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasks");
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
      // Check action buttons for new tasks
      cy.get("tbody tr")
        .first()
        .within(() => {
          cy.get("button").contains("Complete").should("exist");
          cy.get("button[aria-label='More actions']").should("exist");
        });

      // Check that completed tasks don't show action buttons
      cy.get("tbody tr").each(($row) => {
        cy.wrap($row).within(() => {
          cy.get("td").then(($cells) => {
            const statusCell = $cells.eq(1);
            if (statusCell.text().includes("Completed")) {
              cy.get("button").should("not.exist");
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

    it("should handle table filtering by status, system, and request type", () => {
      // Wait for initial data to load
      cy.get("table").should("exist");
      cy.get("tbody tr").should("have.length.at.least", 1);

      // Test status filtering using the custom command
      cy.applyTableFilter("Status", "New");
      cy.get("tbody tr").each(($row) => {
        cy.wrap($row).within(() => {
          cy.getByTestId("manual-task-status-tag").should("contain", "New");
        });
      });

      // Reset filters and test system filtering
      cy.intercept("GET", "/api/v1/manual-tasks*", {
        fixture: "manual-tasks/manual-tasks-response.json",
      }).as("getManualTasksSystem");
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasksSystem");
      cy.get("table").should("exist");
      cy.get("tbody tr").should("have.length.at.least", 1);

      cy.applyTableFilter("System", 0); // Use index for first system option
      cy.get("tbody tr").should("have.length.at.least", 1);

      // Reset filters and test request type filtering
      cy.intercept("GET", "/api/v1/manual-tasks*", {
        fixture: "manual-tasks/manual-tasks-response.json",
      }).as("getManualTasksType");
      cy.visit("/privacy-requests#manual-tasks");
      cy.wait("@getManualTasksType");
      cy.get("table").should("exist");
      cy.get("tbody tr").should("have.length.at.least", 1);

      cy.applyTableFilter("Type", "Access");
      cy.get("tbody tr").each(($row) => {
        cy.wrap($row).within(() => {
          cy.get("td").should("contain", "Access");
        });
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
      cy.wait("@getManualTasks");

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
