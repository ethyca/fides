import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceConfigResponse,
  ExperienceTranslation,
  ExperienceTranslationCreate,
  ExperienceTranslationResponse,
  Language,
  PrivacyNoticeRegion,
  SupportedLanguage,
} from "~/types/api";

import { Layer1ButtonOption } from "./constants";

interface LocationOrLocationGroup {
  selected?: boolean;
  id: string;
  name: string;
}

export const getSelectedRegionIds = (
  allLocations?: LocationOrLocationGroup[],
) =>
  allLocations
    ?.filter((loc) => loc.selected)
    .map((loc) => loc.id as PrivacyNoticeRegion) ?? [];

export const getSelectedRegions = (allLocations?: LocationOrLocationGroup[]) =>
  allLocations?.filter((loc) => loc.selected) ?? [];

export const defaultTranslations: ExperienceTranslationCreate[] = [
  {
    language: SupportedLanguage.EN,
    is_default: true,
    title: "Title",
    description: "Description",
    accept_button_label: "Accept",
    reject_button_label: "Reject",
    save_button_label: "Save",
    acknowledge_button_label: "OK",
    privacy_preferences_link_label: "Privacy Preferences",
  },
];

export const defaultInitialValues: Omit<ExperienceConfigCreate, "component"> = {
  name: "",
  disabled: false,
  dismissable: true,
  allow_language_selection: false,
  show_layer1_notices: false,
  layer1_button_options: Layer1ButtonOption.OPT_IN_OPT_OUT,
  regions: [],
  translations: defaultTranslations,
  auto_detect_language: true,
  auto_subdomain_cookie_deletion: true,
};
// utility type to pass as a prop to the translation form
export type TranslationWithLanguageName = ExperienceTranslation &
  Pick<Language, "name">;

export const findLanguageDisplayName = (
  translation: ExperienceTranslation,
  langs: Language[],
) => {
  const language = langs.find((lang) => lang.id === translation.language);
  return language ? language.name : translation.language;
};

export const transformTranslationResponseToCreate = (
  response: ExperienceTranslationResponse,
): ExperienceTranslationCreate => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { language, is_default, accept_button_label, reject_button_label } =
    response;
  // replace "null"s from the backend with "undefined"s
  return {
    language,
    is_default,
    accept_button_label,
    reject_button_label,
    title: response.title!,
    description: response.description!,
    acknowledge_button_label: response.acknowledge_button_label ?? undefined,
    banner_title: response.banner_title ?? undefined,
    banner_description: response.banner_description ?? undefined,
    purpose_header: response.purpose_header ?? undefined,
    privacy_policy_link_label: response.privacy_policy_link_label ?? undefined,
    privacy_policy_url: response.privacy_policy_url ?? undefined,
    privacy_preferences_link_label:
      response.privacy_preferences_link_label ?? undefined,
    save_button_label: response.save_button_label ?? undefined,
    modal_link_label: response.modal_link_label ?? undefined,
  };
};

export const transformConfigResponseToCreate = (
  config: ExperienceConfigResponse,
): ExperienceConfigCreate => {
  const {
    created_at: createdAt,
    updated_at: updatedAt,
    privacy_notices: notices,
    origin,
    id,
    ...rest
  } = config;
  return {
    ...rest,
    privacy_notice_ids: notices ? notices.map((notice) => notice.id) : [],
    translations: config.translations
      ? config.translations.map((t) => transformTranslationResponseToCreate(t))
      : [],
  };
};

type TranslationFieldConfig = {
  included: boolean;
  required?: boolean;
};

type TranslationFormConfig = {
  [Property in keyof ExperienceTranslationCreate]?: TranslationFieldConfig;
};

export const getTranslationFormFields = (
  component: ComponentType,
): TranslationFormConfig => {
  if (component === ComponentType.PRIVACY_CENTER) {
    return {
      title: { included: true, required: true },
      description: { included: true, required: true },
      save_button_label: { included: true, required: true },
      accept_button_label: { included: true, required: true },
      reject_button_label: { included: true, required: true },
      privacy_policy_link_label: { included: true },
      privacy_policy_url: { included: true },
      modal_link_label: { included: true },
    };
  }
  if (component === ComponentType.MODAL) {
    return {
      title: { included: true, required: true },
      description: { included: true, required: true },
      accept_button_label: { included: true, required: true },
      reject_button_label: { included: true, required: true },
      save_button_label: { included: true, required: true },
      acknowledge_button_label: { included: true, required: true },
      privacy_policy_link_label: { included: true },
      privacy_policy_url: { included: true },
      privacy_preferences_link_label: { included: true },
      modal_link_label: { included: true },
    };
  }

  if (component === ComponentType.BANNER_AND_MODAL) {
    return {
      title: { included: true, required: true },
      banner_title: { included: true },
      description: { included: true, required: true },
      banner_description: { included: true },
      accept_button_label: { included: true, required: true },
      reject_button_label: { included: true, required: true },
      save_button_label: { included: true, required: true },
      acknowledge_button_label: { included: true, required: true },
      privacy_policy_link_label: { included: true },
      privacy_policy_url: { included: true },
      privacy_preferences_link_label: { included: true, required: true },
      modal_link_label: { included: true },
    };
  }

  if (component === ComponentType.TCF_OVERLAY) {
    return {
      title: { included: true, required: true },
      banner_title: { included: true },
      description: { included: true, required: true },
      banner_description: { included: true },
      purpose_header: { included: true },
      accept_button_label: { included: true, required: true },
      reject_button_label: { included: true, required: true },
      save_button_label: { included: true, required: true },
      acknowledge_button_label: { included: true, required: true },
      privacy_policy_link_label: { included: true },
      privacy_policy_url: { included: true },
      privacy_preferences_link_label: { included: true, required: true },
      modal_link_label: { included: true },
    };
  }
  // For default
  return {
    title: { included: true, required: true },
    description: { included: true, required: true },
    accept_button_label: { included: true, required: true },
    reject_button_label: { included: true, required: true },
    save_button_label: { included: true, required: true },
    acknowledge_button_label: { included: true, required: true },
    privacy_policy_link_label: { included: true },
    privacy_policy_url: { included: true },
    privacy_preferences_link_label: { included: true, required: true },
    modal_link_label: { included: true },
  };
};
