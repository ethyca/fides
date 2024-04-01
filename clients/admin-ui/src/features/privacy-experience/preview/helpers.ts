/* eslint-disable*/

import {
  ExperienceConfigCreate,
  ExperienceTranslation,
  PrivacyNoticeResponse,
  SupportedLanguage,
} from "~/types/api";

const defaultTranslation: ExperienceTranslation = {
  language: SupportedLanguage.EN,
  accept_button_label: "Accept",
  acknowledge_button_label: "OK",
  banner_description: "",
  banner_title: "",
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
  config: Partial<ExperienceConfigCreate>
): ExperienceTranslation => ({
  ...defaultTranslation,
  ...(config.translations ? config.translations[0] : {}),
});

export const buildBaseConfig = (
  experienceConfig: Partial<ExperienceConfigCreate>,
  notices: PrivacyNoticeResponse[]
) => ({
  options: {
    debug: false,
    geolocationApiUrl: "",
    isGeolocationEnabled: false,
    isOverlayEnabled: true,
    isPrefetchEnabled: false,
    overlayParentId: "preview-container",
    modalLinkId: null,
    privacyCenterUrl: "http://localhost:3000",
    fidesApiUrl: "http://localhost:8080/api/v1",
    preventDismissal: experienceConfig.dismissable ?? false,
    allowHTMLDescription: true,
    serverSideFidesApiUrl: "",
    fidesString: null,
    fidesJsBaseUrl: "",
    base64Cookie: false,
    fidesLocale: experienceConfig.translations?.[0].language,
  },
  experience: {
    id: "pri_111",
    region: "us_ca",
    component: "banner_and_modal",
    experience_config: {
      id: "pri_222",
      regions: ["us_ca"],
      component: "banner_and_modal",
      disabled: false,
      is_default: true,
      dismissable: experienceConfig.dismissable,
      allow_language_selection: true,
      auto_detect_language: true,
      language: "en",
      // in preview mode, we show the first translation in the main window, even when multiple translations are configured
      translations: [buildExperienceTranslation(experienceConfig)],
    },
    privacy_notices: notices,
  },
  geolocation: {
    country: "US",
    location: "US-CA",
    region: "CA",
  },
});

/**
 * fill in any empty strings in a translation with the defaults from `buildBaseConfig`
 */
export const translationOrDefault = (
  translation: ExperienceTranslation
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
