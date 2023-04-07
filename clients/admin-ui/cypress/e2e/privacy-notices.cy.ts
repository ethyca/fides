import { stubPlus } from "cypress/support/stubs";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const DATA_SALES_NOTICE_ID = "pri_afd25287-cce4-487a-a6b4-b7647b068990";
const ESSENTIAL_NOTICE_ID = "pri_e76cbe20-6ffa-46b4-9a91-b1ae3412dd49";

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
          cy.wait("@getNotices");
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
          cy.wait("@getNotices");
          cy.getByTestId("toggle-Enable")
            .first()
            .within(() => {
              cy.get("span").should("have.attr", "data-disabled");
            });
        }
      );
    });

    it("viewers and approvers cannot add notices", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_NOTICES_ROUTE);
          cy.wait("@getNotices");
          cy.getByTestId("privacy-notices-page");
          cy.getByTestId("add-privacy-notice-btn").should("not.exist");
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
      cy.url().should("contain", ESSENTIAL_NOTICE_ID);
    });

    describe("enabling and disabling", () => {
      beforeEach(() => {
        cy.intercept("PATCH", "/api/v1/privacy-notice*", {
          fixture: "privacy-notices/list.json",
        }).as("patchNotices");
      });

      it("can enable a notice", () => {
        cy.getByTestId("row-Data Sales").within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("not.have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.wait("@patchNotices").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql([{ id: DATA_SALES_NOTICE_ID, disabled: false }]);
        });
        // redux should requery after invalidation
        cy.wait("@getNotices");
      });

      it("can disable a notice with a warning", () => {
        cy.getByTestId("row-Essential").within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.getByTestId("confirmation-modal");
        cy.getByTestId("continue-btn").click();
        cy.wait("@patchNotices").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql([{ id: ESSENTIAL_NOTICE_ID, disabled: true }]);
        });
        // redux should requery after invalidation
        cy.wait("@getNotices");
      });
    });
  });
});
