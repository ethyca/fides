import {
  ExperienceConfigTranslation,
  FidesEndpointPaths,
  FidesInitOptions,
  LegacyConsentConfig,
  PrivacyExperience,
  PrivacyNoticeTranslation,
  UserGeolocation,
} from "fides-js";

import { API_URL } from "./constants";

export const stubIdVerification = () => {
  cy.intercept("GET", `${API_URL}/id-verification/config`, {
    body: {
      identity_verification_required: true,
    },
  }).as("getVerificationConfig");
};

export enum OVERRIDE {
  // signals that we should override entire prop with undefined
  EMPTY = "Empty",
  UNDEFINED = "Undefined",
}

const setNewConfig = (baseConfigObj: any, newConfig: any): any => {
  if (newConfig === OVERRIDE.EMPTY) {
    return {};
  }
  if (newConfig === OVERRIDE.UNDEFINED) {
    return undefined;
  }
  return Object.assign(baseConfigObj, newConfig);
};

interface FidesConfigTesting {
  // We don't need all required props to override the default config
  consent?: Partial<LegacyConsentConfig> | OVERRIDE;
  experience?: Partial<PrivacyExperience> | OVERRIDE;
  geolocation?: Partial<UserGeolocation> | OVERRIDE;
  options: Partial<FidesInitOptions> | OVERRIDE;
}

/**
 * Helper function to override translations for Experience Configs / Notices
 * @example overrideTranslation({language: "en", privacy_experience_config_history_id: "1342314"}, { description: "hello" })
 */
export const overrideTranslation = (
  translation: ExperienceConfigTranslation | PrivacyNoticeTranslation,
  override: Partial<ExperienceConfigTranslation | PrivacyNoticeTranslation>,
): ExperienceConfigTranslation | PrivacyNoticeTranslation => ({
  ...translation,
  ...override,
});
/**
 * Helper function to swap out config
 * @example stubExperience({experience: {component: ComponentType.PRIVACY_CENTER}})
 */
export const stubConfig = (
  { consent, experience, geolocation, options }: Partial<FidesConfigTesting>,
  mockGeolocationApiResp?: any,
  mockExperienceApiResp?: any,
  demoPageQueryParams?: Cypress.VisitOptions["qs"] | null,
  demoPageWindowParams?: any,
) => {
  cy.fixture("consent/fidesjs_options_banner_modal.json").then((config) => {
    const updatedConfig = {
      consent: setNewConfig(config.consent, consent),
      // this mocks the pre-fetched experience
      experience: setNewConfig(config.experience, experience),
      geolocation: setNewConfig(config.geolocation, geolocation),
      options: setNewConfig(config.options, options),
    };
    // We conditionally stub these APIs because we need the exact API urls, which can change or not even exist
    // depending on the specific test case.
    if (
      typeof updatedConfig.options !== "string" &&
      updatedConfig.options?.geolocationApiUrl
    ) {
      const geoLocationResp = setNewConfig(
        {
          body: {
            country: "US",
            ip: "63.173.339.012:13489",
            location: "US-CA",
            region: "CA",
          },
        },
        mockGeolocationApiResp,
      );
      cy.intercept(
        "GET",
        updatedConfig.options.geolocationApiUrl,
        geoLocationResp,
      ).as("getGeolocation");
    }
    if (
      typeof updatedConfig.options !== "string" &&
      updatedConfig.options?.fidesApiUrl
    ) {
      // this mocks the client-side experience fetch
      const experienceMock = mockExperienceApiResp || {
        fixture: "consent/experience_banner_modal.json",
      };
      const experienceResp =
        mockExperienceApiResp === OVERRIDE.UNDEFINED
          ? undefined
          : experienceMock;
      cy.intercept(
        "GET",
        `${updatedConfig.options.fidesApiUrl}${FidesEndpointPaths.PRIVACY_EXPERIENCE}*`,
        experienceResp,
      ).as("getPrivacyExperience");
      cy.intercept("GET", `${API_URL}${FidesEndpointPaths.GVL_TRANSLATIONS}*`, {
        fixture: "consent/gvl_translations.json",
      }).as("getGvlTranslations");
      cy.intercept(
        "PATCH",
        `${updatedConfig.options.fidesApiUrl}${FidesEndpointPaths.PRIVACY_PREFERENCES}`,
        {
          body: {},
        },
      ).as("patchPrivacyPreference");
    }
    cy.intercept(
      "PATCH",
      `${updatedConfig.options.fidesApiUrl}${FidesEndpointPaths.NOTICES_SERVED}`,
      { fixture: "consent/notices_served.json" },
    ).as("patchNoticesServed");
    cy.log("Visiting consent demo with config", updatedConfig);
    cy.visitConsentDemo(
      updatedConfig,
      demoPageQueryParams,
      demoPageWindowParams,
    );
  });
};
