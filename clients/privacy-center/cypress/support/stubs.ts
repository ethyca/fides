import {
  ExperienceConfigTranslation,
  FidesEndpointPaths,
  FidesInitOptions,
  LegacyConsentConfig,
  PrivacyExperience,
  PrivacyExperienceMinimal,
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
  if (!newConfig) {
    return baseConfigObj;
  }
  if (!baseConfigObj) {
    return newConfig;
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
  skipVisit?: boolean,
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
    if (!skipVisit) {
      cy.visitConsentDemo(
        updatedConfig,
        demoPageQueryParams,
        demoPageWindowParams,
      );
    }
  });
};

/**
 * Helper function to stub a TCF experience. This mimics the behavior of loading
 * a minimal experience first, then fetching the full experience. It initializes the
 * normal stubConfig with the minimal experience and then passes the full experience
 * to be used as the mock response for the getPrivacyExperience intercept.
 *
 * @example stubTCFExperience({ experienceConfig: { dismissable: false } })
 *
 * @param stubOptions - Options to override the default FidesJS options
 * @param experienceConfig - Config to override the default experience config
 * @param experienceFullOverride - Override for the full experience
 * @param experienceMinimalOverride - Override for the minimal experience
 * @param mockGeolocationApiResp - Mock response for the geolocation API. This just gets passed along to the stubConfig function as is.
 * @param demoPageQueryParams - Query params to pass to the demo page which passes them to fides.js used to mock customers setting their config via query params in their own script tag.
 * @param demoPageWindowParams - Params to pass to the window object on the demo page used to mock customers setting their config via window object on their own page.
 */
interface StubExperienceTCFProps {
  stubOptions?: Partial<FidesInitOptions>;
  experienceConfig?: Partial<PrivacyExperience["experience_config"]>;
  experienceFullOverride?: Partial<PrivacyExperience>;
  experienceMinimalOverride?: Partial<PrivacyExperienceMinimal>;
  mockGeolocationApiResp?: any;
  demoPageQueryParams?: Cypress.VisitOptions["qs"] | null;
  demoPageWindowParams?: any;
  experienceIsInvalid?: boolean;
  skipVisit?: boolean;
}
export const stubTCFExperience = ({
  stubOptions,
  experienceConfig,
  experienceFullOverride,
  experienceMinimalOverride,
  mockGeolocationApiResp,
  demoPageQueryParams,
  demoPageWindowParams,
  experienceIsInvalid,
  skipVisit,
}: StubExperienceTCFProps) => {
  return cy
    .fixture("consent/experience_tcf_minimal.json")
    .then((experienceMin) => {
      const experienceMinItem = experienceMin.items[0];
      experienceMinItem.experience_config = setNewConfig(
        experienceMinItem.experience_config,
        experienceConfig,
      );
      experienceMin.items[0] = setNewConfig(
        experienceMinItem,
        experienceMinimalOverride,
      );
      cy.fixture("consent/experience_tcf.json").then((experienceFull) => {
        const experienceFullItem = experienceFull.items[0];
        experienceFullItem.experience_config = setNewConfig(
          experienceFullItem.experience_config,
          experienceConfig,
        );
        experienceFull.items[0] = setNewConfig(
          experienceFullItem,
          experienceFullOverride,
        );
        // set initial experience to minimal
        // set stubbed /privacy-experience response to full
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
              ...stubOptions,
            },
            experience: experienceIsInvalid
              ? OVERRIDE.UNDEFINED
              : experienceMinItem,
            geolocation: {
              location: "eea",
              country: "eea",
              region: "fi",
            },
          },
          mockGeolocationApiResp,
          experienceFull,
          demoPageQueryParams,
          demoPageWindowParams,
          skipVisit,
        );
      });
    });
};
