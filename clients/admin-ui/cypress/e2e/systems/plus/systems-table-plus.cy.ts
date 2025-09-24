import {
  stubPlus,
  stubSystemCrud,
  stubSystemGroups,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("systems table plus features", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubPlus(true);
    stubSystemGroups();
    cy.visit(SYSTEM_ROUTE);
    cy.wait("@getSystemsPaginated");
  });

  describe("system groups", () => {
    it("displays system groups column when enabled", () => {
      cy.findAllByRole("columnheader").contains("Groups").should("exist");
    });

    it("allows filtering by system groups", () => {
      cy.get(".ant-table-column-title")
        .contains("Groups")
        .siblings(".ant-dropdown-trigger")
        .click({ force: true });

      cy.get(".ant-table-filter-dropdown:visible").within(() => {
        cy.intercept("GET", "/api/v1/system?**").as("getSystemsByGroup");
        cy.get(".ant-dropdown-menu-item").contains("Blue Group").click();
        cy.get(".ant-dropdown-menu-item").contains("Green Group").click();
        cy.get(".ant-table-filter-dropdown-btns .ant-btn-primary").click();
      });
      cy.url().should("include", "blue_group");
      cy.url().should("include", "green_group");
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

      it("shows system group options in Actions menu when systems are selected", () => {
        cy.contains("button", "Actions").click();
        cy.contains("Add to system group").should("exist");
      });

      it("allows creating new group with selected systems", () => {
        cy.contains("button", "Actions").click();
        cy.contains("Add to system group").trigger("mouseover");
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
      });

      it("allows adding systems to existing group", () => {
        cy.contains("button", "Actions").click();
        cy.contains("Add to system group").click();
        cy.contains("Red Group").click();

        cy.wait("@updateSystemGroup").then((interception) => {
          expect(interception.request.body.systems).to.have.length(3);
          expect(interception.request.body.fides_key).to.exist;
        });
      });
    });
  });
});
