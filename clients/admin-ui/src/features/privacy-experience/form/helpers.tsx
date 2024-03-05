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

interface LocationOrLocationGroup {
  selected?: boolean;
  id: string;
}

export const getSelectedRegionIds = (
  allLocations?: LocationOrLocationGroup[]
) =>
  allLocations
    ?.filter((loc) => loc.selected)
    .map((loc) => loc.id as PrivacyNoticeRegion) ?? [];

export const defaultTranslations: ExperienceTranslationCreate[] = [
  {
    language: SupportedLanguage.EN,
    is_default: true,
    title: "Title",
    description: "Description",
    accept_button_label: "Accept",
    reject_button_label: "Reject",
    privacy_preferences_link_label: "Privacy Preferences",
  },
];

export const defaultInitialValues: Omit<ExperienceConfigCreate, "component"> = {
  disabled: false,
  allow_language_selection: false,
  regions: [],
  translations: defaultTranslations,
};
// utility type to pass as a prop to the translation form
export type TranslationWithLanguageName = ExperienceTranslation &
  Pick<Language, "name">;

export const findLanguageDisplayName = (
  translation: ExperienceTranslation,
  langs: Language[]
) => {
  const language = langs.find((lang) => lang.id === translation.language);
  return language ? language.name : translation.language;
};

export const transformTranslationResponseToCreate = (
  response: ExperienceTranslationResponse
): ExperienceTranslationCreate => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { privacy_experience_config_history_id, ...rest } = response;
  return {
    ...rest,
    description: response.description ?? "",
    title: response.title ?? "",
  };
};

export const transformConfigResponseToCreate = (
  config: ExperienceConfigResponse
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
  component: ComponentType
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
    };
  }
  if (component === ComponentType.MODAL) {
    return {
      title: { included: true, required: true },
      description: { included: true, required: true },
      accept_button_label: { included: true, required: true },
      reject_button_label: { included: true, required: true },
      acknowledge_button_label: { included: true },
      privacy_policy_link_label: { included: true },
      privacy_policy_url: { included: true },
      privacy_preferences_link_label: { included: true },
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
      acknowledge_button_label: { included: true },
      privacy_policy_link_label: { included: true },
      privacy_policy_url: { included: true },
      privacy_preferences_link_label: { included: true },
    };
  }
  return {
    title: { included: true, required: true },
    description: { included: true, required: true },
    accept_button_label: { included: true, required: true },
    reject_button_label: { included: true, required: true },
    save_button_label: { included: true },
    acknowledge_button_label: { included: true },
    privacy_policy_link_label: { included: true },
    privacy_policy_url: { included: true },
    privacy_preferences_link_label: { included: true },
  };
};
