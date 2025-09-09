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
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";
import { ComponentType, SupportedLanguage } from "~/types/api";

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
        cy.getByTestId("controlled-select-component").antSelect(
          "Banner and modal",
        );
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").antSelect(0);
        cy.getByTestId("add-location").click();

        cy.getByTestId("select-location").antSelect("France");
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

      it("doesn't show a preview for a privacy center", () => {
        cy.getByTestId("controlled-select-component").antSelect(
          "Privacy center",
        );
        cy.getByTestId("input-dismissable").should("not.be.visible");
        cy.getByTestId("no-preview-notice").contains(
          "Privacy center preview not available",
        );
      });

      it("doesn't show preview until privacy notice is added", () => {
        cy.getByTestId("controlled-select-component").antSelect(
          "Banner and modal",
        );
        cy.getByTestId("no-preview-notice").contains(
          "No privacy notices added",
        );
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").antSelect(0);
        cy.getByTestId("no-preview-notice").should("not.exist");
        cy.get(`#${PREVIEW_CONTAINER_ID}`).should("be.visible");
      });

      it("shows option to display privacy notices in banner and updates preview when clicked", () => {
        cy.getByTestId("input-show_layer1_notices").should("not.exist");
        cy.getByTestId("controlled-select-component").antSelect(
          "Banner and modal",
        );
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").antSelect(0);
        cy.getByTestId("input-show_layer1_notices").click();
        cy.get("#preview-container")
          .find("#fides-banner")
          .find("#fides-banner-notices")
          .contains("Data Sales and Sharing");
      });

      it("does not show option to display privacy notices in modal preview when clicked", () => {
        cy.getByTestId("input-show_layer1_notices").should("not.exist");
        cy.getByTestId("controlled-select-component").antSelect("Modal");
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").antSelect(0);
        cy.getByTestId("input-show_layer1_notices").should("not.exist");
      });

      it("allows editing experience text and shows updated text in the preview", () => {
        cy.getByTestId("controlled-select-component").antSelect(
          "Banner and modal",
        );
        cy.getByTestId("add-privacy-notice").click();
        cy.getByTestId("select-privacy-notice").antSelect(0);
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

      it("doesn't allow component type to be changed", () => {
        cy.getByTestId("controlled-select-component").should(
          "have.class",
          "ant-select-disabled",
        );
        cy.getByTestId("input-dismissable").should("be.visible");
      });

      it("populates the form and shows the preview with the existing values", () => {
        cy.wait("@getExperienceDetail");
        cy.getByTestId("controlled-select-component").should(
          "have.class",
          "ant-select-disabled",
        );
        cy.getByTestId("input-name").should(
          "have.value",
          "Example modal experience",
        );
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Manage your consent preferences",
        );
      });

      it("shows a preview while editing TCF experience", () => {
        cy.fixture("privacy-experiences/experienceConfig.json").then((data) => {
          cy.intercept("GET", "/api/v1/experience-config/pri*", {
            ...data,
            component: "tcf_overlay",
          }).as("getTCFExperience");
        });
        cy.wait("@getTCFExperience");
        cy.getByTestId("input-dismissable").should("be.visible");
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Manage your consent preferences",
        );
      });

      it("shows a notification when vendor count is zero for TCF overlay", () => {
        // Mock vendor report with zero vendors
        cy.intercept(
          {
            method: "GET",
            pathname: "/api/v1/system",
            query: {
              page: "1",
              size: "1",
            },
          },
          {
            items: [],
            total: 0,
            page: 1,
            size: 1,
          },
        ).as("getVendorReportEmpty");

        cy.fixture("privacy-experiences/experienceConfig.json").then((data) => {
          cy.intercept("GET", "/api/v1/experience-config/pri*", {
            ...data,
            component: "tcf_overlay",
          }).as("getTCFExperience");
        });

        cy.wait("@getTCFExperience");
        cy.wait("@getVendorReportEmpty");

        // Check that the notification appears
        cy.get(".ant-notification-notice")
          .should("be.visible")
          .within(() => {
            cy.contains("No vendors available");
          });
      });

      it("can edit the TCF configuration for a TCF experience", () => {
        cy.intercept("GET", "/api/v1/config*", {
          body: {
            consent: {
              override_vendor_purposes: true,
            },
          },
        });
        // Load a TCF experience that already has a config assigned
        cy.fixture("privacy-experiences/experienceConfig.json").then((data) => {
          cy.intercept("GET", "/api/v1/experience-config/pri_001", {
            ...data,
            id: "pri_001",
            component: "tcf_overlay",
            tcf_configuration_id: "tcf_config_1", // Assign initial config
          }).as("getTCFExperience");
        });
        cy.intercept("PATCH", "/api/v1/experience-config/pri_001", {
          fixture: "privacy-experiences/experienceConfig.json",
        }).as("patchExperience");

        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/pri_001`);
        cy.wait("@getTCFExperience");
        cy.wait("@getTcfConfigs"); // Make sure configs are loaded

        // Verify the select is visible and has the initial value
        cy.getByTestId("controlled-select-tcf_configuration_id")
          .should("be.visible")
          .contains("Default TCF Config");

        // Change the TCF config
        cy.getByTestId("controlled-select-tcf_configuration_id").antSelect(
          "Strict TCF Config",
        );
        cy.getByTestId("save-btn").click();
        cy.wait("@patchExperience").then((interception) => {
          const { body } = interception.request;
          expect(body.tcf_configuration_id).to.eql("tcf_config_2");
        });
        cy.getByTestId("toast-success-msg").should("exist");

        // Clear the TCF config
        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/pri_001`); // Re-visit to reset state
        cy.wait("@getTCFExperience");
        cy.wait("@getTcfConfigs");
        cy.getByTestId("controlled-select-tcf_configuration_id")
          .should("be.visible")
          .find(".ant-select-clear")
          .click();
        cy.getByTestId("save-btn").click();
        cy.wait("@patchExperience").then((interception) => {
          const { body } = interception.request;
          // Depending on backend behavior, this might be null or undefined
          expect(body.tcf_configuration_id).to.be.oneOf([null, undefined]);
        });
        cy.getByTestId("toast-success-msg").should("exist");
      });

      it("disables the TCF Publisher Override configuration when the consent override is disabled", () => {
        cy.intercept("GET", "/api/v1/config*", {
          body: {
            consent: {
              override_vendor_purposes: false,
            },
          },
        });
        // Load a TCF experience that already has a config assigned
        cy.fixture("privacy-experiences/experienceConfig.json").then((data) => {
          cy.intercept("GET", "/api/v1/experience-config/pri_001", {
            ...data,
            id: "pri_001",
            component: "tcf_overlay",
            tcf_configuration_id: "tcf_config_1", // Assign initial config
          }).as("getTCFExperience");
        });
        cy.intercept("PATCH", "/api/v1/experience-config/pri_001", {
          fixture: "privacy-experiences/experienceConfig.json",
        }).as("patchExperience");

        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/pri_001`);
        cy.wait("@getTCFExperience");
        cy.wait("@getTcfConfigs"); // Make sure configs are loaded
        cy.getByTestId("controlled-select-tcf_configuration_id")
          .should("be.visible")
          .should("have.class", "ant-select-disabled");
      });

      it("disables the TCF Publisher Override configuration when there are no TCF configs", () => {
        cy.intercept("GET", "/api/v1/config*", {
          body: {
            consent: {
              override_vendor_purposes: true,
            },
          },
        });
        // Load a TCF experience that already has a config assigned
        cy.fixture("privacy-experiences/experienceConfig.json").then((data) => {
          cy.intercept("GET", "/api/v1/experience-config/pri_001", {
            ...data,
            id: "pri_001",
            component: "tcf_overlay",
          }).as("getTCFExperience");
        });
        cy.intercept("GET", "/api/v1/plus/tcf/configurations*", {
          items: [],
        }).as("getTcfConfigs");

        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/pri_001`);
        cy.wait("@getTCFExperience");
        cy.wait("@getTcfConfigs"); // Make sure configs are loaded
        cy.getByTestId("controlled-select-tcf_configuration_id")
          .should("be.visible")
          .should("have.class", "ant-select-disabled");
      });
    });

    describe("editing translations", () => {
      beforeEach(() => {
        stubTranslationConfig(true);
        stubPrivacyNoticesCrud();
        stubLocations();
        stubProperties();
        cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/pri_001`);
        cy.wait("@getExperienceDetail");
      });

      it("shows the preview for the translation currently being edited", () => {
        cy.getByTestId("language-row-fr").realHover();
        cy.getByTestId("edit-language-row-fr").click({ force: true });
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Gestion du consentement et des préférences",
        );
      });

      it("allows discarding unsaved changes after showing a modal", () => {
        cy.getByTestId("language-row-en").realHover();
        cy.getByTestId("edit-language-row-en").click({ force: true });
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
        cy.getByTestId("language-row-fr").realHover();
        cy.getByTestId("edit-language-row-fr").click({ force: true });
        cy.getByTestId("input-translations.1.is_default").click();
        cy.getByTestId("save-btn").click();
        cy.getByTestId("warning-modal-confirm-btn").click();
        cy.getByTestId("language-row-fr").contains("(Default)");
        cy.get(`#${PREVIEW_CONTAINER_ID}`).contains(
          "Gestion du consentement et des préférences",
        );
      });

      it("can add new translations with all required fields", () => {
        const components = [
          { type: ComponentType.MODAL, displayName: "Modal" },
          {
            type: ComponentType.BANNER_AND_MODAL,
            displayName: "Banner and modal",
          },
          { type: ComponentType.PRIVACY_CENTER, displayName: "Privacy center" },
          { type: ComponentType.HEADLESS, displayName: "Headless" },
          { type: ComponentType.TCF_OVERLAY, displayName: "TCF overlay" },
        ];

        components.forEach(({ type, displayName }) => {
          // Create new experience with the component type
          cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/new`);
          cy.getByTestId("input-name").type(`${displayName} Test`);
          cy.getByTestId("controlled-select-component").antSelect(displayName);
          cy.getByTestId("add-privacy-notice").click();
          cy.getByTestId("select-privacy-notice").antSelect(0);
          cy.getByTestId("add-location").click();
          cy.getByTestId("select-location").antSelect("France");

          // Add translations for both languages
          [SupportedLanguage.EN_GB, SupportedLanguage.FR_CA].forEach(
            (language) => {
              // Add new translation
              cy.getByTestId("add-language").click();
              cy.getByTestId("select-language").antSelect(
                language === "en-GB" ? "English (UK)" : "French (Canada)",
              );

              // Fill out all required fields with 'Test'
              const typeOptions = { delay: 50 };
              cy.getByTestId("privacy-experience-detail-page")
                .find("input[required], textarea[required]")
                .each(($input) => {
                  cy.wrap($input).type(`Test ${language}`, typeOptions);
                });

              // Verify preview displays the new translation
              if (
                [
                  ComponentType.BANNER_AND_MODAL,
                  ComponentType.MODAL,
                  ComponentType.TCF_OVERLAY,
                ].includes(type)
              ) {
                cy.getByTestId("fides-modal-title")
                  .contains(`Test ${language}`)
                  .should("exist");
              }

              // Verify save button is enabled
              cy.getByTestId("save-btn").should("not.be.disabled");

              // Save the translation
              cy.getByTestId("save-btn").click();

              // Verify the translation was added
              cy.getByTestId(`language-row-${language}`).should("exist");
            },
          );

          // Save the experience
          cy.getByTestId("save-btn").click();
          cy.url().should("match", /privacy-experience$/);
          cy.getByTestId("toast-success-msg").should("exist");
        });
      });

      it("Can add translations to a TCF experience after filling required fields", () => {
        // Intercept the TCF experience response
        cy.intercept("GET", "/api/v1/experience-config/*", {
          fixture: "privacy-experiences/tcf-experience.json",
        }).as("getTCFExperience");

        // Visit the TCF experience page
        cy.visit(
          `${PRIVACY_EXPERIENCE_ROUTE}/pri_f5eb2be4-95e3-45cc-9c82-9a4bd0d64182`,
        );
        cy.wait("@getTCFExperience");

        // Add new translation
        cy.getByTestId("add-language").click();
        cy.getByTestId("select-language").antSelect("French (Canada)");

        // Fill out all required fields with 'Test'
        const typeOptions = { delay: 50 };
        cy.getByTestId("privacy-experience-detail-page")
          .find("input[required], textarea[required]")
          .each(($input) => {
            cy.wrap($input).type("Test", typeOptions);
          });

        // Verify save button is enabled
        cy.getByTestId("save-btn").should("not.be.disabled");

        // Save the translation
        cy.getByTestId("save-btn").click();

        // Verify the translation was added
        cy.getByTestId("language-row-fr-CA").should("exist");
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
