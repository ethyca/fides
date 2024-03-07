/* eslint-disable*/

import {
  ExperienceConfigCreate,
  ExperienceTranslation,
  PrivacyNoticeResponse,
  SupportedLanguage,
} from "~/types/api";

const defaultTranslation = {
  language: SupportedLanguage.EN,
  accept_button_label: "Accept",
  acknowledge_button_label: "OK",
  banner_description: "",
  banner_title: "",
  description: "",
  privacy_policy_link_label: "",
  privacy_policy_url: "",
  privacy_preferences_link_label: "",
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

export enum FidesPreviewComponent {
  BANNER = "banner",
  MODAL = "modal",
}

export const buildBaseConfig = (
  experienceConfig: Partial<ExperienceConfigCreate>,
  notices: PrivacyNoticeResponse[]
) => ({
  options: {
    debug: true,
    geolocationApiUrl: "",
    isGeolocationEnabled: false,
    isOverlayEnabled: true,
    isPrefetchEnabled: false,
    overlayParentId: "preview-container",
    modalLinkId: null,
    privacyCenterUrl: "http://localhost:3000",
    fidesApiUrl: "http://localhost:8080/api/v1",
    // todo- get this from config
    preventDismissal: experienceConfig.dismissable ?? false,
    fidesPreviewMode: true,
    fidesPreviewComponent: FidesPreviewComponent.BANNER,
    allowHTMLDescription: true,
    serverSideFidesApiUrl: "",
    fidesString: null,
    fidesJsBaseUrl: "",
    base64Cookie: false,
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

// fill in any empty strings in a translations with the defaults above
export const translationOrDefault = (
  translation: ExperienceTranslation
): ExperienceTranslation => {
  const { language, is_default, ...textFields } = translation;
  const newTextFields = Object.entries(textFields)
    .map(([key, value]) => ({
      [key]: !!value
        ? value
        : defaultTranslation[key as keyof ExperienceTranslation],
    }))
    .reduce((acc, current) => ({ ...acc, ...current }), {});
  return { language, is_default, ...newTextFields };
};
