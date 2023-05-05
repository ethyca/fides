import { stubPlus } from "cypress/support/stubs";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const OVERLAY_EXPERIENCE_ID = "pri_4076d6dd-a728-4f2d-9a5c-98f35d7a5a86";
const DISABLED_EXPERIENCE_ID = "pri_75d2b3dc-6f7c-4a36-95ee-3088bd1b4572";

describe("Privacy experiences", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/privacy-experience*", {
      fixture: "privacy-experiences/list.json",
    }).as("getExperiences");
    stubPlus(true);
  });

  describe("permissions", () => {
    it("should not be viewable for approvers", () => {
      cy.assumeRole(RoleRegistryEnum.APPROVER);
      cy.visit(PRIVACY_EXPERIENCE_ROUTE);
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
        cy.visit(PRIVACY_EXPERIENCE_ROUTE);
        cy.getByTestId("privacy-experience-page");
      });
    });

    it("viewers and approvers cannot click into an experience to edit", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_EXPERIENCE_ROUTE);
          cy.wait("@getExperiences");
          cy.getByTestId(`row-${OVERLAY_EXPERIENCE_ID}`).click();
          // we should still be on the same page
          cy.getByTestId("privacy-experience-detail-page").should("not.exist");
          cy.getByTestId("privacy-experience-page");
        }
      );
    });

    it("viewers and approvers cannot toggle the enable toggle", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_EXPERIENCE_ROUTE);
          cy.wait("@getExperiences");
          cy.getByTestId("toggle-Enable")
            .first()
            .within(() => {
              cy.get("span").should("have.attr", "data-disabled");
            });
        }
      );
    });
  });

  it("can show an empty state", () => {
    cy.intercept("GET", "/api/v1/privacy-experience*", {
      body: { items: [], page: 1, size: 10, total: 0 },
    }).as("getEmptyExperiences");
    cy.visit(PRIVACY_EXPERIENCE_ROUTE);
    cy.wait("@getEmptyExperiences");
    cy.getByTestId("empty-state");
  });

  describe("table", () => {
    beforeEach(() => {
      cy.visit(PRIVACY_EXPERIENCE_ROUTE);
      cy.wait("@getExperiences");
    });

    it("should render a row for each privacy experience", () => {
      cy.fixture("privacy-experiences/list.json").then((data) => {
        data.items
          .map((item) => item.id)
          .forEach((id) => {
            cy.getByTestId(`row-${id}`);
          });
      });
    });

    it("can click a row to go to the experience page", () => {
      cy.intercept("GET", "/api/v1/privacy-experience/pri*", {
        fixture: "privacy-experiences/experience.json",
      }).as("getExperienceDetail");
      cy.getByTestId(`row-${OVERLAY_EXPERIENCE_ID}`).click();
      cy.wait("@getExperienceDetail");
      cy.getByTestId("privacy-experience-detail-page");
      cy.url().should("contain", OVERLAY_EXPERIENCE_ID);
    });

    describe("enabling and disabling", () => {
      beforeEach(() => {
        cy.intercept("PATCH", "/api/v1/privacy-experience*", {
          fixture: "privacy-experiences/list.json",
        }).as("patchExperiences");
      });

      it("can enable an experience", () => {
        cy.getByTestId(`row-${DISABLED_EXPERIENCE_ID}`).within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("not.have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.wait("@patchExperiences").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql([
            { id: DISABLED_EXPERIENCE_ID, disabled: false },
          ]);
        });
        // redux should requery after invalidation
        cy.wait("@getExperiences");
      });

      it("can disable an experience with a warning", () => {
        cy.getByTestId(`row-${OVERLAY_EXPERIENCE_ID}`).within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.getByTestId("confirmation-modal");
        cy.getByTestId("continue-btn").click();
        cy.wait("@patchExperiences").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql([{ id: OVERLAY_EXPERIENCE_ID, disabled: true }]);
        });
        // redux should requery after invalidation
        cy.wait("@getExperiences");
      });
    });
  });
});
