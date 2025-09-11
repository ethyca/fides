import {
  stubPlus,
  stubSystemCrud,
  stubUserManagement,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("systems table", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubPlus(false);
    stubUserManagement();
    cy.visit(SYSTEM_ROUTE);
    cy.wait("@getSystemsPaginated");
  });

  describe("table display and navigation", () => {
    it("displays systems in a table format", () => {
      cy.getAntTableRow("fidesctl_system").should("exist");
      cy.getAntTableRow("demo_analytics_system").should("exist");
    });

    it("allows clicking on system name to navigate to system details", () => {
      cy.getAntTableRow("fidesctl_system").within(() => {
        cy.getByTestId("system-link-fidesctl_system").click();
      });
      cy.url().should("include", "/systems/configure/fidesctl_system");
    });
  });

  describe("filtering", () => {
    it("filters systems by data steward", () => {
      cy.intercept("/api/v1/system?**").as("getSystemsBySteward");
      cy.applyTableFilter("Data steward", "user_3");
      cy.get(".ant-table-filter-dropdown").within(() => {
        cy.get(".ant-btn-primary").click({ force: true });
        cy.wait("@getSystemsBySteward").then((interception) => {
          expect(interception.request.query.data_steward).to.eql("user_3");
        });
      });
    });
  });

  describe("row selection and bulk actions", () => {
    beforeEach(() => {
      cy.getAntTableRow("fidesctl_system")
        .find("input[type='checkbox']")
        .click();
      cy.getAntTableRow("demo_analytics_system")
        .find("input[type='checkbox']")
        .click({ force: true });
    });

    it("allows bulk assigning data steward", () => {
      cy.contains("button", "Actions").click();
      cy.contains("Assign data steward").trigger("mouseover");
      cy.get("li").contains("user_1").click();
      cy.wait("@bulkAssignSteward").then((interception) => {
        expect(interception.request.body.system_keys).to.have.length(2);
      });
    });

    it("allows bulk deletion of systems", () => {
      cy.contains("button", "Actions").click();
      cy.contains("Delete").click();
      cy.contains("button", "Delete").click();
      cy.wait("@bulkDeleteSystems").then((interception) => {
        expect(interception.request.body).to.have.length(2);
      });
    });
  });

  describe("individual system actions", () => {
    it("allows editing individual system", () => {
      cy.getAntTableRow("fidesctl_system").within(() => {
        cy.get("button[aria-label='More actions']").click();
      });
      cy.contains("Edit").click();
      cy.url().should("include", "/systems/configure/fidesctl_system");
    });

    it("allows deleting individual system", () => {
      cy.getAntTableRow("fidesctl_system").within(() => {
        cy.get("button[aria-label='More actions']").click();
      });
      cy.contains("Delete").click();
      cy.contains("button", "Delete").click();
      cy.wait("@deleteSystem");
    });
  });

  describe("table column display", () => {
    it("displays all required columns", () => {
      const expectedColumns = [
        "Name",
        "Data uses",
        "Data steward",
        "Description",
        "Actions",
      ];
      expectedColumns.forEach((column) => {
        cy.findAllByRole("columnheader").contains(column).should("exist");
      });
    });
  });
});
