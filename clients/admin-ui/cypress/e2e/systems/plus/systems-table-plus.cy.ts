import { stubPlus, stubSystemCrud } from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("systems table plus features", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubPlus(true);
    cy.visit(SYSTEM_ROUTE);
    cy.wait("@getSystemsPaginated");
  });

  describe("system groups", () => {
    beforeEach(() => {
      // Stub system groups data
      cy.intercept("GET", "/api/v1/system_group", {
        fixture: "systems/system_groups.json",
      }).as("getSystemGroups");
    });

    it("displays system groups column when enabled", () => {
      cy.get("[data-column-key='system_groups']").should("exist");
    });

    it("shows system groups in the table", () => {
      cy.getAntTableRow("fidesctl_system").within(() => {
        cy.get("[data-column-key='system_groups']").should("exist");
      });
    });

    it("allows filtering by system groups", () => {
      cy.get("[data-column-key='system_groups']")
        .find(".ant-table-filter-trigger")
        .click();
      cy.get(".ant-dropdown-menu-item").first().click();
      cy.wait("@getSystemsPaginated").then((interception) => {
        expect(interception.request.query.system_group).to.exist;
      });
    });

    describe("bulk actions on groups", () => {
      beforeEach(() => {
        cy.getAntTableRow("fidesctl_system")
          .find("input[type='checkbox']")
          .click();
        cy.getAntTableRow("demo_analytics_system")
          .find("input[type='checkbox']")
          .click();
      });

      it("enables 'Add to group' button when systems are selected", () => {
        cy.contains("button", "Add to group").should("be.enabled");
      });

      it("allows creating new group with selected systems", () => {
        cy.contains("button", "Add to group").click();
        cy.contains("Create new group +").click();

        cy.getByTestId("input-name").type("Test Group");
        cy.getByTestId("input-description").type("Test group description");
        cy.getByTestId("save-btn").click();

        cy.wait("@createSystemGroup").then((interception) => {
          expect(interception.request.body).to.deep.include({
            name: "Test Group",
            description: "Test group description",
          });
          expect(interception.request.body.systems).to.have.length(2);
        });
        cy.getByTestId("toast-success-msg").should("exist");
      });

      it("allows adding systems to existing group", () => {
        cy.contains("button", "Add to group").click();

        cy.get(".ant-dropdown-menu-item").eq(1).click();

        cy.wait("@bulkUpdateSystemGroups").then((interception) => {
          expect(interception.request.body.system_keys).to.have.length(2);
          expect(interception.request.body.group_key).to.exist;
        });
        cy.getByTestId("toast-success-msg").should("exist");
      });

      it("shows error message when bulk add to group fails", () => {
        cy.intercept("PUT", "/api/v1/system/bulk_update_groups", {
          statusCode: 500,
          body: { detail: "Server error" },
        }).as("bulkUpdateError");

        cy.contains("button", "Add to group").click();
        cy.get(".ant-dropdown-menu-item").eq(1).click();
        cy.wait("@bulkUpdateError");
        cy.getByTestId("toast-error-msg").should("exist");
      });
    });

    describe("group column display", () => {
      it("shows expand/collapse controls for groups", () => {
        cy.get("[data-column-key='system_groups']").within(() => {
          cy.get(".ant-table-column-title").click();
          cy.contains("Expand all").click();
          cy.contains("Collapse all").click();
        });
      });

      it("allows expanding individual system groups", () => {
        cy.getAntTableRow("fidesctl_system").within(() => {
          cy.get("[data-column-key='system_groups']")
            .find(".ant-table-row-expand-icon")
            .click();
        });
      });
    });

    describe("create system group modal", () => {
      beforeEach(() => {
        cy.contains("button", "Add to group").click();
        cy.contains("Create new group +").click();
      });

      it("validates required fields", () => {
        cy.getByTestId("save-btn").click();
        cy.contains("Name is required").should("exist");
      });

      it("shows selected systems count", () => {
        cy.contains("2 systems selected").should("exist");
      });

      it("allows canceling group creation", () => {
        cy.getByTestId("cancel-btn").click();
        cy.get(".ant-modal").should("not.exist");
      });

      it("shows error when group creation fails", () => {
        cy.intercept("POST", "/api/v1/system_group", {
          statusCode: 500,
          body: { detail: "Server error" },
        }).as("createGroupError");

        cy.getByTestId("input-name").type("Test Group");
        cy.getByTestId("save-btn").click();
        cy.wait("@createGroupError");
        cy.getByTestId("toast-error-msg").should("exist");
      });
    });
  });
});
