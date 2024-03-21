import { stubPlus, stubTranslationConfig } from "cypress/support/stubs";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const EXPERIENCE_ID = "pri_0338d055-f91b-4a17-ad4e-600c61551199";
const DISABLED_EXPERIENCE_ID = "pri_8fd9d334-e625-4365-ba25-9c368f0b1231";

describe("Privacy experiences", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/experience-config*", {
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
          cy.get("table").contains("tr", "notice enabled test").click();
          // we should still be on the same page
          cy.getByTestId("privacy-experience-detail-page").should("not.exist");
          cy.getByTestId("privacy-experience-page");
        }
      );
    });

    it("viewers and approvers cannot see toggle the enable toggle", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PRIVACY_EXPERIENCE_ROUTE);
          cy.wait("@getExperiences");
          cy.get(".toggle").should("not.exist");
        }
      );
    });
  });

  it("can show an empty state", () => {
    cy.intercept("GET", "/api/v1/experience-config*", {
      body: { items: [], page: 1, size: 10, total: 0 },
    }).as("getEmptyExperiences");
    cy.visit(PRIVACY_EXPERIENCE_ROUTE);
    cy.wait("@getEmptyExperiences");
    cy.getByTestId("empty-state");
  });

  it("can copy a JS script tag", () => {
    cy.visit(PRIVACY_EXPERIENCE_ROUTE);
    cy.getByTestId("js-tag-btn").click();
    cy.getByTestId("copy-js-tag-modal");
    // Have to use a "real click" in order for Cypress to properly inspect
    // the window's clipboard https://github.com/cypress-io/cypress/issues/18198
    cy.getByTestId("clipboard-btn").realClick();
    cy.window().then((win) => {
      win.navigator.clipboard.readText().then((text) => {
        expect(text).to.contain("<script src=");
      });
    });
  });

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
      cy.intercept("GET", "/api/v1/experience-config/pri*", {
        fixture: "privacy-experiences/experienceConfig.json",
      }).as("getExperienceDetail");
      cy.get("table").contains("tr", "notice enabled test").click();
      cy.wait("@getExperienceDetail");
      cy.getByTestId("input-name").should("have.value", "Experience title");
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
            cy.getByTestId("toggle-switch").within(() => {
              cy.get("span").should("have.attr", "data-checked");
            });
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

  describe("forms", () => {
    beforeEach(() => {
      cy.intercept("PATCH", "/api/v1/experience-config/*", {
        fixture: "privacy-experiences/experienceConfig.json",
      }).as("patchExperience");
    });
    /**
     * Helper function to swap out the component type in a stubbed experience
     * @example stubExperience({component: "overlay"})
     */
    const stubExperience = () => {
      cy.intercept("GET", "/api/v1/experience-config/pri*", {
        fixture: "privacy-experiences/experienceConfig.json",
      });
    };

    it.skip("can populate an experience config form with existing values", () => {
      stubExperience();
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${EXPERIENCE_ID}`);
      cy.getByTestId("input-name").should("have.value", "notice enabled test");
    });

    it.skip("can submit an experience config form", () => {
      stubExperience();
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${EXPERIENCE_ID}`);
      cy.getByTestId("save-btn").should("be.disabled");
      cy.getByTestId("input-name").clear().type("New experience title");
      cy.getByTestId("save-btn").click();
      cy.wait("@patchExperience").then((interception) => {
        const { body } = interception.request;
        expect(body.name).to.eql("New experience title");
        // Make sure regions is still ["us_ca"] (unchanged)
        expect(body.regions).to.eql(["us_ca"]);
      });
    });
  });

  describe("translation interface", () => {
    it("shows the language interface when translations are enabled", () => {
      stubTranslationConfig(true);
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/new`);
      cy.wait("@getTranslationConfig");
      cy.getByTestId("input-auto_detect_language").should("exist");
    });

    it("shows an edit button instead when translations are disabled", () => {
      stubTranslationConfig(false);
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/new`);
      cy.wait("@getTranslationConfig");
      cy.getByTestId("input-auto_detect_language").should("not.exist");
      cy.getByTestId("edit-experience-btn").should("exist");
    });
  });
});
