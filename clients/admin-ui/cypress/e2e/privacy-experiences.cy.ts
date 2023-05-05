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

  describe("form", () => {
    beforeEach(() => {
      cy.intercept("PATCH", "/api/v1/privacy-experience*", {
        fixture: "privacy-experiences/list.json",
      }).as("patchExperiences");
    });
    interface Props {
      mechanisms: ("opt_in" | "opt_out" | "notice_only")[];
      component?: "overlay" | "privacy_center";
    }
    /**
     * Helper function to swap out notices and components in a stubbed experience
     * @example stubExperience({mechanisms: ["notice_only", "opt_in"], component: "overlay"})
     */
    const stubExperience = ({ mechanisms, component }: Props) => {
      const notices = [];
      mechanisms.forEach((mechanism) => {
        cy.fixture(`privacy-notices/${mechanism}.json`).then((notice) =>
          notices.push(notice)
        );
      });
      cy.fixture("privacy-experiences/experience.json").then((experience) => {
        const updatedExperience = {
          ...experience,
          privacy_notices: mechanisms ? notices : experience.privacy_notices,
          component: component ?? experience.component,
        };
        cy.intercept("GET", "/api/v1/privacy-experience/pri*", {
          body: updatedExperience,
        });
      });
    };

    it("renders opt_in notice with banner as delivery mechanism", () => {
      stubExperience({ mechanisms: ["opt_in"], component: "overlay" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.getByTestId("privacy-center-messaging-form").should("not.exist");

      cy.getByTestId("delivery-mechanism-form").within(() => {
        cy.getSelectValueContainer("input-delivery_mechanism").within(() => {
          cy.get("input").should("be.disabled");
        });
        cy.getSelectValueContainer("input-delivery_mechanism").should(
          "contain",
          "Banner"
        );
      });
      cy.getByTestId("banner-text-form");
      cy.getByTestId("banner-action-form");
    });

    it("renders notice_only notice with acknowledgment btn and banner as mechanism", () => {
      stubExperience({ mechanisms: ["notice_only"], component: "overlay" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.getByTestId("privacy-center-messaging-form").should("not.exist");

      cy.getByTestId("delivery-mechanism-form").within(() => {
        cy.getSelectValueContainer("input-delivery_mechanism").within(() => {
          cy.get("input").should("be.disabled");
        });
        cy.getSelectValueContainer("input-delivery_mechanism").should(
          "contain",
          "Banner"
        );
      });
      cy.getByTestId("banner-text-form");
      cy.getByTestId("banner-action-form").within(() => {
        cy.getByTestId("input-confirmation_button_label").should("not.exist");
        cy.getByTestId("input-reject_button_label").should("not.exist");
        cy.getByTestId("input-acknowledgement_button_label");
      });
    });

    it("renders notice_only combined with other notices with confirm/reject btns", () => {
      stubExperience({
        mechanisms: ["notice_only", "opt_in"],
        component: "overlay",
      });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.getByTestId("privacy-center-messaging-form").should("not.exist");

      cy.getByTestId("delivery-mechanism-form");
      cy.getByTestId("banner-text-form");
      cy.getByTestId("banner-action-form").within(() => {
        cy.getByTestId("input-confirmation_button_label");
        cy.getByTestId("input-reject_button_label");
        cy.getByTestId("input-acknowledgement_button_label").should(
          "not.exist"
        );
      });
    });

    it("renders opt_out notice with all options available", () => {
      stubExperience({ mechanisms: ["opt_out"], component: "overlay" });
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
        mechanisms: ["opt_in", "opt_out", "notice_only"],
        component: "privacy_center",
      });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      cy.getByTestId("privacy-center-messaging-form");
      cy.getByTestId("delivery-mechanism-form").should("not.exist");
      cy.getByTestId("banner-text-form").should("not.exist");
      cy.getByTestId("banner-action-form").should("not.exist");
    });

    it("can submit an overlay form", () => {
      // opt_out is the most permissive, so use that one
      stubExperience({ mechanisms: ["opt_out"], component: "overlay" });
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
        cy.getByTestId(`input-${key}`).type(value);
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@patchExperiences").then((interception) => {
        const { body } = interception.request;
        Object.entries(payload).forEach(([key, value]) => {
          expect(body[0][key]).to.eql(value);
        });
      });
    });

    it("can submit a privacy center form", () => {
      stubExperience({ mechanisms: ["opt_out"], component: "privacy_center" });
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/${OVERLAY_EXPERIENCE_ID}`);
      const payload = {
        link_label: "link label",
        component_description: "title",
      };
      Object.entries(payload).forEach(([key, value]) => {
        cy.getByTestId(`input-${key}`).type(value);
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@patchExperiences").then((interception) => {
        const { body } = interception.request;
        Object.entries(payload).forEach(([key, value]) => {
          expect(body[0][key]).to.eql(value);
        });
      });
    });
  });
});
