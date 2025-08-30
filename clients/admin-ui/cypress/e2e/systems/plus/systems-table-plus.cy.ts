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
      cy.intercept("/api/v1/system?**").as("getSystemsByGroup");
      cy.applyTableFilter("Groups", "Blue Group");
      cy.wait("@getSystemGroups");
      cy.get(".ant-table-filter-dropdown").within(() => {
        cy.findByRole("button", { name: "OK" }).click({ force: true });
        cy.wait("@getSystemsByGroup").then((interception) => {
          expect(interception.request.query.system_group).to.exist;
        });
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
      });

      it("allows adding systems to existing group", () => {
        cy.contains("button", "Add to group").click();

        cy.get(".ant-dropdown-menu-item").eq(1).click();

        cy.wait("@updateSystemGroup").then((interception) => {
          expect(interception.request.body.systems).to.have.length(4);
          expect(interception.request.body.fides_key).to.exist;
        });
      });
    });
  });
});
