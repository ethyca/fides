import { stubPlus } from "cypress/support/stubs";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("Privacy notices", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/privacy-notice*", {
      fixture: "privacy-notices/list.json",
    }).as("getNotices");
    stubPlus(true);
  });

  describe("permissions", () => {
    it("should not be viewable for approvers", () => {
      cy.assumeRole(RoleRegistryEnum.APPROVER);
      cy.visit(PRIVACY_NOTICES_ROUTE);
      // should be redirected to the home page
      cy.getByTestId("home-content");
    });

    it("should be visible to everyone else", () => {
      [
        RoleRegistryEnum.CONTRIBUTOR,
        RoleRegistryEnum.OWNER,
        RoleRegistryEnum.VIEWER,
      ].forEach((role) => {
        cy.assumeRole(role);
        cy.visit(PRIVACY_NOTICES_ROUTE);
        cy.getByTestId("privacy-notices-page");
      });
    });

    it("viewers and approvers cannot click into a notice to edit", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_NOTICES_ROUTE);
          cy.getByTestId("row-Essential").click();
          // we should still be on the same page
          cy.getByTestId("privacy-notice-detail-page").should("not.exist");
          cy.getByTestId("privacy-notices-page");
        }
      );
    });

    it("viewers and approvers cannot toggle the enable toggle", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_NOTICES_ROUTE);
          cy.getByTestId("toggle-Enable").should("be.disabled");
        }
      );
    });
  });

  describe("table", () => {
    beforeEach(() => {
      cy.visit(PRIVACY_NOTICES_ROUTE);
      cy.wait("@getNotices");
    });

    it("should render a row for each privacy notice", () => {
      [
        "Essential",
        "Functional",
        "Analytics",
        "Advertising",
        "Data Sales",
      ].forEach((name) => {
        cy.getByTestId(`row-${name}`);
      });
    });

    it("can sort", () => {
      cy.get("tbody > tr").first().should("contain", "Data Sales");
      // sort alphabetical
      cy.getByTestId("column-Title").click();
      cy.get("tbody > tr").first().should("contain", "Advertising");

      // sort reverse
      cy.getByTestId("column-Title").click();
      cy.get("tbody > tr").first().should("contain", "Functional");
    });

    it("can click a row to go to the notice page", () => {
      cy.getByTestId("row-Essential").click();
      cy.getByTestId("privacy-notice-detail-page");
      cy.url().should("contain", "pri_e76cbe20-6ffa-46b4-9a91-b1ae3412dd49");
    });
  });
});
