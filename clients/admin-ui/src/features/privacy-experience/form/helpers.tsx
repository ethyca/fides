import {
  // ComponentType,
  ExperienceConfigCreate,
  ExperienceConfigResponse,
  ExperienceTranslationCreate,
  ExperienceTranslationResponse,
  SupportedLanguage,
} from "~/types/api";

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

export const transformTranslationResponseToCreate = (
  response: ExperienceTranslationResponse
): ExperienceTranslationCreate => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { experience_config_history_id, ...rest } = response;
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
