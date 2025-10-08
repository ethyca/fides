import {
  stubExperienceConfig,
  stubFidesCloud,
  stubLocations,
  stubPrivacyNoticesCrud,
  stubProperties,
  stubTranslationConfig,
} from "cypress/support/stubs";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";

const EXPERIENCE_ID = "pri_0338d055-f91b-4a17-ad4e-600c61551199";
const DISABLED_EXPERIENCE_ID = "pri_8fd9d334-e625-4365-ba25-9c368f0b1231";

describe("Privacy experiences", () => {
  beforeEach(() => {
    cy.login();
    stubProperties();
    stubExperienceConfig();
    stubFidesCloud();
    stubPrivacyNoticesCrud();
    stubTranslationConfig(false);
    stubLocations();
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
        cy.wait("@getExperiences");
        cy.getByTestId("privacy-experience-page");
      });
    });

    it("viewers and approvers cannot click into an experience to edit", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_EXPERIENCE_ROUTE);
          cy.wait("@getExperiences");
          cy.get("table").contains("tr", "notice enabled test").click();
          // we should still be on the same page
          cy.getByTestId("privacy-experience-detail-page").should("not.exist");
          cy.getByTestId("privacy-experience-page");
        },
      );
    });

    it("viewers and approvers cannot see toggle the enable toggle", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_EXPERIENCE_ROUTE);
          cy.wait("@getExperiences");
          cy.get(".toggle").should("not.exist");
        },
      );
    });
  });

  it("can show an empty state", () => {
    cy.intercept("GET", "/api/v1/experience-config*", {
      fixture: "empty-pagination.json",
    }).as("getEmptyExperiences");
    cy.visit(PRIVACY_EXPERIENCE_ROUTE);
    cy.wait("@getEmptyExperiences");
    cy.getByTestId("empty-state");
  });

  if (Cypress.isBrowser({ family: "chromium" })) {
    it("can copy a JS script tag", () => {
      cy.visit(PRIVACY_EXPERIENCE_ROUTE);
      cy.getByTestId("js-tag-btn").click();
      cy.getByTestId("copy-js-tag-modal");
      // Have to use a "real click" in order for Cypress to properly inspect
      // the window's clipboard https://github.com/cypress-io/cypress/issues/18198
      cy.getByTestId("clipboard-btn").first().realClick();
      cy.window().then((win) => {
        win.navigator.clipboard.readText().then((text) => {
          expect(text).to.contain("<script src=");
        });
      });
    });
  }

  describe("table", () => {
    beforeEach(() => {
      cy.visit(PRIVACY_EXPERIENCE_ROUTE);
      cy.wait("@getExperiences");
    });

    it("should render a row for each privacy experience", () => {
      cy.fixture("privacy-experiences/list.json").then((data) => {
        data.items.forEach((item, index) => {
          cy.getByTestId(`row-${index}`);
        });
      });
    });

    it("can click a row to go to the experience page", () => {
      cy.get("table").contains("tr", "notice enabled test").click();
      cy.wait("@getExperienceDetail");
      cy.getByTestId("input-name").should(
        "have.value",
        "Example modal experience",
      );
    });

    it("can click the button to create a new experience", () => {
      cy.getByTestId("add-privacy-experience-btn").click();
      cy.url().should("contain", "privacy-experience/new");
    });

    describe("enabling and disabling", () => {
      beforeEach(() => {
        cy.intercept("PATCH", "/api/v1/experience-config/*/limited_update", {
          fixture: "privacy-experiences/experienceConfig.json",
        }).as("patchExperience");
      });

      it("can enable an experience", () => {
        cy.get("table")
          .contains("tr", "notice disabled test")
          .within(() => {
            cy.getByTestId("toggle-switch").within(() => {
              cy.get("span").should("not.have.attr", "data-checked");
            });
            cy.getByTestId("toggle-switch").click();
          });

        cy.wait("@patchExperience").then((interception) => {
          const { body, url } = interception.request;
          expect(url).to.contain(DISABLED_EXPERIENCE_ID);
          expect(body).to.eql({ disabled: false });
        });
        // redux should requery after invalidation
        cy.wait("@getExperiences");
      });

      it("can disable an experience with a warning", () => {
        cy.get("table")
          .contains("tr", "notice enabled test")
          .within(() => {
            cy.getByTestId("toggle-switch").should(
              "have.attr",
              "aria-checked",
              "true",
            );
            cy.getByTestId("toggle-switch").click();
          });

        cy.getByTestId("confirmation-modal");
        cy.getByTestId("continue-btn").click();
        cy.wait("@patchExperience").then((interception) => {
          const { body, url } = interception.request;
          expect(url).to.contain(EXPERIENCE_ID);
          expect(body).to.eql({ disabled: true });
        });
        // redux should requery after invalidation
        cy.wait("@getExperiences");
      });
    });
  });
});
