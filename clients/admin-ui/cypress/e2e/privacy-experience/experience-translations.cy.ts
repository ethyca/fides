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
import { ComponentType, SupportedLanguage } from "~/types/api";

describe("Experience translations", () => {
  beforeEach(() => {
    cy.login();
    stubProperties();
    stubExperienceConfig();
    stubFidesCloud();
    stubPrivacyNoticesCrud();
    stubTranslationConfig(true);
    stubLocations();
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
    cy.getByTestId("input-translations.0.title").clear();
    cy.getByTestId("input-translations.0.title").type("Other");
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

    components.forEach(({ type, displayName }, index) => {
      // Create new experience with the component type
      cy.visit(`${PRIVACY_EXPERIENCE_ROUTE}/new`);
      cy.getByTestId("input-name").type(`Test ${index}`);
      cy.getByTestId("controlled-select-component").antSelect(displayName);
      cy.getByTestId("add-privacy-notice").click();
      cy.getByTestId("select-privacy-notice").antSelect(0);
      cy.getByTestId("add-location").click();
      cy.getByTestId("select-location").antSelect("France");

      // Add translations for both languages
      [SupportedLanguage.EN_GB, SupportedLanguage.FR_CA].forEach((language) => {
        // Add new translation
        cy.getByTestId("add-language").click();
        cy.getByTestId("select-language").antSelect(
          language === "en-GB" ? "English (UK)" : "French (Canada)",
        );

        // Fill out all required fields with 'Test'
        cy.getByTestId("privacy-experience-detail-page")
          .find("input[required], textarea[required]")
          .each(($input) => {
            cy.wrap($input).type(`Test ${language}`);
          });

        // Verify preview displays the new translation
        if (
          [
            ComponentType.BANNER_AND_MODAL,
            ComponentType.MODAL,
            ComponentType.TCF_OVERLAY,
          ].includes(type)
        ) {
          cy.get("#fides-modal-title")
            .contains(`Test ${language}`)
            .should("exist");
        }

        // Verify save button is enabled
        cy.getByTestId("save-btn").should("not.be.disabled");

        // Save the translation
        cy.getByTestId("save-btn").click();

        // Verify the translation was added
        cy.getByTestId(`language-row-${language}`).should("exist");
      });

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
    cy.getByTestId("privacy-experience-detail-page")
      .find("input[required], textarea[required]")
      .each(($input) => {
        cy.wrap($input).type("Test");
      });

    // Verify save button is enabled
    cy.getByTestId("save-btn").should("not.be.disabled");

    // Save the translation
    cy.getByTestId("save-btn").click();

    // Verify the translation was added
    cy.getByTestId("language-row-fr-CA").should("exist");
  });
});
