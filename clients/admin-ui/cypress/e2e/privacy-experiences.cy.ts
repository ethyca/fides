import { stubPlus } from "cypress/support/stubs";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const OVERLAY_EXPERIENCE_ID = "pri_33fd622e-a63a-4847-b910-3b3fdf8c109f";
const DISABLED_EXPERIENCE_ID = "pri_66b689cb-44ae-4124-8ae8-7dc6d79eff84";

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
        data.items
          .map((item) => item.id)
          .forEach((id) => {
            cy.getByTestId(`row-${id}`);
          });
      });
    });

    it("can click a row to go to the experience page", () => {
      cy.intercept("GET", "/api/v1/experience-config/pri*", {
        fixture: "privacy-experiences/experienceConfig.json",
      }).as("getExperienceDetail");
      cy.getByTestId(`row-${OVERLAY_EXPERIENCE_ID}`).click();
      cy.wait("@getExperienceDetail");
      cy.getByTestId("privacy-experience-detail-page");
      cy.url().should("contain", OVERLAY_EXPERIENCE_ID);
    });

    describe("enabling and disabling", () => {
      beforeEach(() => {
        cy.intercept("PATCH", "/api/v1/experience-config/*", {
          fixture: "privacy-experiences/experienceConfig.json",
        }).as("patchExperience");
      });

      it("can enable an experience", () => {
        cy.getByTestId(`row-${DISABLED_EXPERIENCE_ID}`).within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("not.have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.wait("@patchExperience").then((interception) => {
          const { body, url } = interception.request;
          expect(url).to.contain(DISABLED_EXPERIENCE_ID);
          expect(body).to.eql({ disabled: false, regions: ["eu_fr", "eu_ie"] });
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
        cy.wait("@patchExperience").then((interception) => {
          const { body, url } = interception.request;
          expect(url).to.contain(OVERLAY_EXPERIENCE_ID);
          expect(body).to.eql({ disabled: true, regions: ["us_ca"] });
        });
        // redux should requery after invalidation
        cy.wait("@getExperiences");
      });
    });
  });

  describe("form", () => {
    beforeEach(() => {
      cy.intercept("PATCH", "/api/v1/experience-config/*", {
        fixture: "privacy-experiences/experienceConfig.json",
      }).as("patchExperience");
    });
    interface Props {
      component?: "overlay" | "privacy_center";
    }
    /**
     * Helper function to swap out notices and components in a stubbed experience
     * @example stubExperience({component: "overlay"})
     */
    const stubExperience = ({ component }: Props) => {
      cy.fixture("privacy-experiences/experienceConfig.json").then(
        (experience) => {
          const updatedExperience = {
            ...experience,
            component: component ?? experience.component,
          };
          cy.intercept("GET", "/api/v1/experience-config/pri*", {
            body: updatedExperience,
          });
        }
      );
    };

    it("renders opt_out notice with all options available", () => {
      stubExperience({ component: "overlay" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.getByTestId("privacy-center-messaging-form").should("not.exist");

      cy.getByTestId("delivery-mechanism-form").within(() => {
        cy.getSelectValueContainer("input-delivery_mechanism").within(() => {
          cy.get("input").should("not.be.disabled");
        });
      });
      cy.getByTestId("banner-text-form");
      cy.getByTestId("banner-action-form");
    });

    it("renders privacy center overlays without banner form sections", () => {
      stubExperience({
        component: "privacy_center",
      });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.getByTestId("privacy-center-messaging-form");
      cy.getByTestId("delivery-mechanism-form").should("not.exist");
      cy.getByTestId("banner-text-form").should("not.exist");
      cy.getByTestId("banner-action-form").should("not.exist");
    });

    it("can submit an overlay form", () => {
      stubExperience({ component: "overlay" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);

      const payload = {
        delivery_mechanism: "banner",
        banner_title: "title",
        banner_description: "description",
        link_label: "link label",
        confirmation_button_label: "Accept",
        reject_button_label: "Reject",
      };
      cy.selectOption("input-delivery_mechanism", "Banner");
      Object.entries(payload).forEach(([key, value]) => {
        if (key !== "delivery_mechanism") {
          cy.getByTestId(`input-${key}`).clear().type(value);
        }
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@patchExperience").then((interception) => {
        const { body } = interception.request;
        Object.entries(payload).forEach(([key, value]) => {
          expect(body[key]).to.eql(value);
        });
      });
    });

    it("can submit a privacy center form", () => {
      stubExperience({ component: "privacy_center" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      const payload = {
        link_label: "link label",
        component_description: "title",
      };
      Object.entries(payload).forEach(([key, value]) => {
        cy.getByTestId(`input-${key}`).clear().type(value);
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@patchExperience").then((interception) => {
        const { body } = interception.request;
        Object.entries(payload).forEach(([key, value]) => {
          expect(body[key]).to.eql(value);
        });
      });
    });
  });
});
