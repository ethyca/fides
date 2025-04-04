/* eslint-disable*/

import { PREVIEW_CONTAINER_ID } from "~/constants";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
  Layer1ButtonOption,
  PrivacyNoticeResponse,
  SupportedLanguage,
} from "~/types/api";

const defaultTranslation: ExperienceTranslation = {
  language: SupportedLanguage.EN,
  accept_button_label: "Accept",
  acknowledge_button_label: "OK",
  banner_description: "",
  banner_title: "",
  purpose_header: "",
  description: "Description",
  privacy_policy_link_label: "",
  privacy_policy_url: "",
  modal_link_label: "",
  privacy_preferences_link_label: "Privacy preferences",
  reject_button_label: "Reject All",
  save_button_label: "Save",
  title: "Manage your consent preferences",
  is_default: true,
};

export const buildExperienceTranslation = (
  config: Partial<ExperienceConfigCreate>,
): ExperienceTranslation => ({
  ...defaultTranslation,
  ...(config.translations ? config.translations[0] : {}),
});

export const buildBaseConfig = (
  experienceConfig: Partial<ExperienceConfigCreate>,
  notices: PrivacyNoticeResponse[],
) => {
  const baseConfig: any = {
    options: {
      allowHTMLDescription: true,
      base64Cookie: false,
      debug: false,
      fidesApiUrl: "http://localhost:8080/api/v1",
      fidesClearCookie: true,
      fidesDisableSaveApi: true,
      fidesDisableNoticesServedApi: true,
      fidesJsBaseUrl: "",
      fidesLocale: experienceConfig.translations?.[0]?.language,
      fidesString: null,
      geolocationApiUrl: "",
      isGeolocationEnabled: false,
      isOverlayEnabled: true,
      isPrefetchEnabled: false,
      modalLinkId: null,
      overlayParentId: PREVIEW_CONTAINER_ID,
      preventDismissal: experienceConfig.dismissable ?? false,
      privacyCenterUrl: "http://localhost:3000",
      showFidesBrandLink: true,
    },
    experience: {
      available_locales: experienceConfig.translations?.map((t) => t.language),
      component: experienceConfig.component,
      experience_config: {
        allow_language_selection: true,
        auto_detect_language: true,
        auto_subdomain_cookie_deletion: true,
        component: experienceConfig.component,
        disabled: false,
        dismissable: experienceConfig.dismissable,
        id: "pri_222",
        is_default: true,
        language: "en",
        layer1_button_options: Layer1ButtonOption.OPT_IN_OPT_OUT,
        properties: [],
        regions: ["us_ca"],
        show_layer1_notices: false,
        // in preview mode, we show the first translation in the main window, even when multiple translations are configured
        translations: [buildExperienceTranslation(experienceConfig)],
      },
      id: "pri_111",
      privacy_notices: notices,
      region: "us_ca",
    },
    geolocation: {
      country: "US",
      location: "US-CA",
      region: "CA",
    },
  };
  if (experienceConfig.component === ComponentType.TCF_OVERLAY) {
    baseConfig.options.fidesTcfGdprApplies = true;
    baseConfig.options.tcf_enabled = true;
    baseConfig.geolocation = { location: "eea", country: "eea" };
    baseConfig.experience.experience_config.regions = ["eea"];
    baseConfig.experience = {
      ...baseConfig.experience,
      ...{
        region: "eea",
        minimal_tcf: true,
        gvl: { vendors: {} },
        tcf_purpose_names: [
          // DEFERRED (LJ-614): replace with applicable purpose names from new endpoint
          "Store and/or access information on a device",
          "Use limited data to select advertising",
          "Create profiles for personalised advertising",
          "Use profiles to select personalised advertising",
          "Create profiles to personalise content",
          "Use profiles to select personalised content",
          "Measure advertising performance",
          "Measure content performance",
          "Understand audiences through statistics or combinations of data from different sources",
          "Develop and improve services",
          "Use limited data to select content",
        ],
      },
    };
    baseConfig.options.apiOptions = {
      getPrivacyExperienceFn: async () => {
        return baseConfig.experience;
      },
    };
  }
  return baseConfig;
};

/**
 * fill in any empty strings in a translation with the defaults from `buildBaseConfig`
 */
export const translationOrDefault = (
  translation: ExperienceTranslation,
): ExperienceTranslation => {
  const { language, is_default, ...textFields } = defaultTranslation;
  const newTextFields = Object.keys(textFields)
    .map((key) => {
      const value = translation[key as keyof ExperienceTranslation];
      return {
        [key]:
          value !== undefined
            ? value
            : defaultTranslation[key as keyof ExperienceTranslation],
      };
    })
    .reduce((acc, current) => ({ ...acc, ...current }), {});
  return {
    language: translation.language,
    is_default: translation.is_default,
    ...newTextFields,
  };
};
