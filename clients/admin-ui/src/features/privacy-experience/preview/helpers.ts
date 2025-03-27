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
) => ({
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
    fidesTcfGdprApplies:
      experienceConfig.component === ComponentType.TCF_OVERLAY,
    geolocationApiUrl: "",
    isGeolocationEnabled: false,
    isOverlayEnabled: true,
    isPrefetchEnabled: false,
    modalLinkId: null,
    overlayParentId: PREVIEW_CONTAINER_ID,
    preventDismissal: experienceConfig.dismissable ?? false,
    privacyCenterUrl: "http://localhost:3000",
    showFidesBrandLink: true,
    tcf_enabled: experienceConfig.component === ComponentType.TCF_OVERLAY,
  },
  experience: {
    available_locales: experienceConfig.translations?.map((t) => t.language),
    component: "banner_and_modal",
    experience_config: {
      allow_language_selection: true,
      auto_detect_language: true,
      auto_subdomain_cookie_deletion: true,
      component: "banner_and_modal",
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
    gvl: {},
    gvl_translations: {},
    id: "pri_111",
    privacy_notices: notices,
    region: "us_ca",
    tcf_purpose_consents: [],
    tcf_purpose_legitimate_interests: [],
    tcf_special_purposes: [],
    tcf_features: [],
    tcf_special_features: [],
    tcf_vendor_consents: [],
    tcf_vendor_legitimate_interests: [],
    tcf_vendor_relationships: [],
    tcf_system_consents: [],
    tcf_system_legitimate_interests: [],
    tcf_system_relationships: [],
    tcf_publisher_country_code: null,
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
