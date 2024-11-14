import {
  stubExperienceConfig,
  stubFidesCloud,
  stubLanguages,
  stubLocations,
  stubPrivacyNoticesCrud,
  stubProperties,
  stubTranslationConfig,
} from "cypress/support/stubs";

import { PREVIEW_CONTAINER_ID } from "~/constants";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const EXPERIENCE_ID = "pri_0338d055-f91b-4a17-ad4e-600c61551199";
const DISABLED_EXPERIENCE_ID = "pri_8fd9d334-e625-4365-ba25-9c368f0b1231";

describe("Privacy experiences", () => {
  beforeEach(() => {
    cy.login();
    stubProperties();
    stubExperienceConfig();
    stubFidesCloud();
    stubLanguages();
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

  describe("forms", () => {
    describe("creating a new experience config", () => {
      beforeEach(() => {
        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/new`);
        cy.wait("@getNotices");
      });

      it("can create an experience", () => {
        cy.getByTestId("input-name").type("Test experience name");
        cy.selectOption("input-component", "Banner and modal");
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").click();
        cy.get(".select-privacy-notice__menu")
          .find(".select-privacy-notice__option")
          .first()
          .click();
        cy.getByTestId("add-location").click();
        cy.getByTestId("select-location").click();
        cy.get(".select-location__menu")
          .find(".select-location__option")
          .first()
          .click();
        cy.intercept("POST", "/api/v1/experience-config", {
          statusCode: 200,
        }).as("postExperience");
        cy.getByTestId("save-btn").click();
        cy.wait("@postExperience").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql({
            allow_language_selection: false,
            auto_detect_language: true,
            auto_subdomain_cookie_deletion: true,
            component: "banner_and_modal",
            disabled: true,
            dismissable: true,
            name: "Test experience name",
            layer1_button_options: "opt_in_opt_out",
            show_layer1_notices: false,
            privacy_notice_ids: ["pri_b1244715-2adb-499f-abb2-e86b6c0040c2"],
            regions: ["fr"],
            translations: [
              {
                accept_button_label: "Accept",
                acknowledge_button_label: "OK",
                description: "Description",
                is_default: true,
                language: "en",
                privacy_preferences_link_label: "Privacy Preferences",
                reject_button_label: "Reject",
                save_button_label: "Save",
                title: "Title",
              },
            ],
          });
        });
        cy.url().should("match", /privacy-experience$/);
        cy.getByTestId("toast-success-msg").should("exist");
      });

      it("doesn't allow component type to be changed after selection", () => {
        cy.selectOption("input-component", "Banner and modal");
        cy.getByTestId("input-component").find("input").should("be.disabled");
        cy.getByTestId("input-dismissable").should("be.visible");
      });

      it("doesn't show a preview for a privacy center", () => {
        cy.selectOption("input-component", "Privacy center");
        cy.getByTestId("input-dismissable").should("not.be.visible");
        cy.getByTestId("no-preview-notice").contains(
          "Privacy center preview not available",
        );
      });

      it("doesn't show preview until privacy notice is added", () => {
        cy.selectOption("input-component", "Banner and modal");
        cy.getByTestId("no-preview-notice").contains(
          "No privacy notices added",
        );
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").click();
        cy.get(".select-privacy-notice__menu")
          .find(".select-privacy-notice__option")
          .first()
          .click();
        cy.getByTestId("no-preview-notice").should("not.exist");
        cy.get(`#${PREVIEW_CONTAINER_ID}`).should("be.visible");
      });

      it("shows option to display privacy notices in banner and updates preview when clicked", () => {
        cy.getByTestId("input-show_layer1_notices").should("not.be.visible");
        cy.selectOption("input-component", "Banner and modal");
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").click();
        cy.get(".select-privacy-notice__menu")
          .find(".select-privacy-notice__option")
          .first()
          .as("SelectedPrivacyNotice")
          .click();
        cy.getByTestId("input-show_layer1_notices").click();
        cy.get("#preview-container")
          .find("#fides-banner")
          .find("#fides-banner-notices")
          .contains("Essential");
      });

      it("allows editing experience text and shows updated text in the preview", () => {
        cy.selectOption("input-component", "Banner and modal");
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").click();
        cy.get(".select-privacy-notice__menu")
          .find(".select-privacy-notice__option")
          .first()
          .click();
        cy.getByTestId("edit-experience-btn").click();
        cy.getByTestId("input-translations.0.title")
          .clear()
          .type("Edited title");
        cy.getByTestId("save-btn").click();
        cy.get(`#${PREVIEW_CONTAINER_ID}`)
          .find("#fides-banner")
          .contains("Edited title");
      });
    });

    describe("editing an existing experience config", () => {
      beforeEach(() => {
        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/pri_001`);
      });

      it("populates the form and shows the preview with the existing values", () => {
        cy.wait("@getExperienceDetail");
        cy.getByTestId("input-component").find("input").should("be.disabled");
        cy.getByTestId("input-name").should(
          "have.value",
          "Example modal experience",
        );
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Manage your consent preferences",
        );
      });

      it("doesn't show a preview while editing TCF experience", () => {
        cy.fixture("privacy-experiences/experienceConfig.json").then((data) => {
          cy.intercept("GET", "/api/v1/experience-config/pri*", {
            ...data,
            component: "tcf_overlay",
          }).as("getTCFExperience");
        });
        cy.wait("@getTCFExperience");
        cy.getByTestId("input-dismissable").should("be.visible");
        cy.getByTestId("no-preview-notice").contains(
          "TCF preview not available",
        );
      });
    });

    describe("editing translations", () => {
      beforeEach(() => {
        stubTranslationConfig(true);
        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/pri_001`);
        cy.wait("@getExperienceDetail");
      });

      it("shows the preview for the translation currently being edited", () => {
        cy.getByTestId("language-row-fr").click();
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Gestion du consentement et des préférences",
        );
      });

      it("allows discarding unsaved changes after showing a modal", () => {
        cy.getByTestId("language-row-en").click();
        cy.getByTestId("input-translations.0.title")
          .clear()
          .type("Some other title");
        cy.getByTestId("cancel-btn").click();
        cy.getByTestId("warning-modal-confirm-btn").click();
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Manage your consent preferences",
        );
      });

      it("allows changing the default language after showing a modal", () => {
        cy.getByTestId("language-row-fr").click();
        cy.getByTestId("input-translations.1.is_default").click();
        cy.getByTestId("save-btn").click();
        cy.getByTestId("warning-modal-confirm-btn").click();
        cy.getByTestId("language-row-fr").contains("(Default)");
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Gestion du consentement et des préférences",
        );
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
