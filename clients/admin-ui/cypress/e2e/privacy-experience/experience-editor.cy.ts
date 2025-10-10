import {
  stubExperienceConfig,
  stubFidesCloud,
  stubLocations,
  stubPrivacyNoticesCrud,
  stubProperties,
  stubTranslationConfig,
} from "cypress/support/stubs";

import { PREVIEW_CONTAINER_ID } from "~/constants";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";

describe("Experience editor", () => {
  beforeEach(() => {
    cy.login();
    stubProperties();
    stubExperienceConfig();
    stubFidesCloud();
    stubPrivacyNoticesCrud();
    stubTranslationConfig(false);
    stubLocations();
  });

  describe("creating a new experience config", () => {
    beforeEach(() => {
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/new`);
      cy.wait("@getNotices");
    });

    it("can create an experience", () => {
      cy.getByTestId("input-name").type("Test");
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
        expect(body).to.deep.include({
          allow_language_selection: false,
          auto_detect_language: true,
          auto_subdomain_cookie_deletion: true,
          allow_vendor_asset_disclosure: false,
          component: "banner_and_modal",
          disabled: true,
          dismissable: true,
          name: "Test",
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
      cy.getByTestId("controlled-select-component").antSelect("Privacy center");
      cy.getByTestId("input-dismissable").should("not.be.visible");
      cy.getByTestId("no-preview-notice").contains(
        "Privacy center preview not available",
      );
    });

    it("doesn't show preview until privacy notice is added", () => {
      cy.getByTestId("controlled-select-component").antSelect(
        "Banner and modal",
      );
      cy.getByTestId("no-preview-notice").contains("No privacy notices added");
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
      cy.getByTestId("input-translations.0.title").clear();
      cy.getByTestId("input-translations.0.title").type("Edit");
      cy.getByTestId("save-btn").click();
      cy.get(`#${PREVIEW_CONTAINER_ID}`).find("#fides-banner").contains("Edit");
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
        "GET",
        "/api/v1/plus/system/consent-management/report?page=1&size=1",
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
