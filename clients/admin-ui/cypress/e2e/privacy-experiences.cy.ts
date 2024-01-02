import { stubPlus } from "cypress/support/stubs";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const OVERLAY_EXPERIENCE_ID = "pri_0338d055-f91b-4a17-ad4e-600c61551199";
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

    it("should show default experience as 'Global'", () => {
      cy.getByTestId(`row-${OVERLAY_EXPERIENCE_ID}`).within(() => {
        cy.get("td").first().contains("Global");
      });
      cy.getByTestId(`row-${DISABLED_EXPERIENCE_ID}`).within(() => {
        cy.get("td").first().contains("California (USA)");
      });
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
          expect(body).to.eql({ disabled: false });
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
    interface Props {
      component?: "overlay" | "privacy_center";
    }
    /**
     * Helper function to swap out the component type in a stubbed experience
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

    it("can populate an overlay form with existing values", () => {
      stubExperience({ component: "overlay" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.fixture("privacy-experiences/experienceConfig.json").then(
        (experience) => {
          const keys = [
            "title",
            "description",
            "banner_title",
            "banner_description",
            "privacy_preferences_link_label",
            "save_button_label",
            "accept_button_label",
            "reject_button_label",
            "acknowledge_button_label",
            "privacy_policy_link_label",
            "privacy_policy_url",
          ];
          keys.forEach((key) => {
            cy.getByTestId(`input-${key}`).should(
              "have.value",
              experience[key]
            );
          });
          cy.getSelectValueContainer("input-banner_enabled").contains(
            "Always disabled"
          );
        }
      );
    });

    it("can populate a privacy center form with existing values", () => {
      stubExperience({ component: "privacy_center" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.fixture("privacy-experiences/experienceConfig.json").then(
        (experience) => {
          const keys = [
            "title",
            "description",
            "save_button_label",
            "accept_button_label",
            "reject_button_label",
            "privacy_policy_link_label",
            "privacy_policy_url",
          ];
          keys.forEach((key) => {
            cy.getByTestId(`input-${key}`).should(
              "have.value",
              experience[key]
            );
          });
        }
      );
    });

    it("can submit an overlay form", () => {
      stubExperience({ component: "overlay" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);

      const payload = {
        title: "title",
        description: "description",
        banner_title: "banner title",
        banner_description: "banner description",
        privacy_preferences_link_label: "Manage your preferences",
        save_button_label: "Save now",
        accept_button_label: "Accept",
        reject_button_label: "Reject",
        acknowledge_button_label: "Alright",
        privacy_policy_link_label: "Check out our privacy policy",
        privacy_policy_url: "https://example.com/privacy-policy",
        banner_enabled: "enabled_where_required",
      };
      cy.selectOption("input-banner_enabled", "Enabled where legally required");
      Object.entries(payload).forEach(([key, value]) => {
        if (key !== "banner_enabled") {
          cy.getByTestId(`input-${key}`).clear().type(value);
        }
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@patchExperience").then((interception) => {
        const { body } = interception.request;
        Object.entries(payload).forEach(([key, value]) => {
          expect(body[key]).to.eql(value);
        });
        // Make sure regions is still ["us_ca"] (unchanged)
        expect(body.regions).to.eql(["us_ca"]);
      });
    });

    it("can submit an overlay form excluding optional values", () => {
      stubExperience({ component: "overlay" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);

      const payload = {
        title: "title",
        description: "description",
        privacy_preferences_link_label: "Manage your preferences",
        save_button_label: "Save now",
        accept_button_label: "Accept",
        reject_button_label: "Reject",
        acknowledge_button_label: "Alright",
        banner_enabled: "enabled_where_required",
      };
      const optionalFields = [
        "banner_title",
        "banner_description",
        "privacy_policy_link_label",
        "privacy_policy_url",
      ];
      cy.selectOption("input-banner_enabled", "Enabled where legally required");
      Object.entries(payload).forEach(([key, value]) => {
        if (key !== "banner_enabled") {
          cy.getByTestId(`input-${key}`).clear().type(value);
        }
      });
      optionalFields.forEach((key) => {
        cy.getByTestId(`input-${key}`).clear();
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@patchExperience").then((interception) => {
        const { body } = interception.request;
        Object.entries(payload).forEach(([key, value]) => {
          expect(body[key]).to.eql(value);
        });
        // Ensure we set these explicitly to "null" so the API understands they are cleared
        optionalFields.forEach((key) => {
          expect(body[key]).to.eql(null);
        });
      });
    });

    it("can submit a privacy center form", () => {
      stubExperience({ component: "privacy_center" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      const payload = {
        title: "New title",
        description: "New description",
        save_button_label: "Save now",
        accept_button_label: "Accept",
        reject_button_label: "Reject",
        privacy_policy_link_label: "Check out our privacy policy",
        privacy_policy_url: "https://example.com/privacy-policy",
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
        // Make sure regions is still ['us_ca'] (unchanged)
        expect(body.regions).to.eql(["us_ca"]);
      });
    });
  });
});
