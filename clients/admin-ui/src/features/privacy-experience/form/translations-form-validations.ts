import * as Yup from "yup";

import { ExperienceTranslationCreate } from "~/types/api";

export type FieldValidationData = {
  label: string;
  validation: Yup.Schema;
};

export const FIELD_VALIDATION_DATA: Record<
  keyof ExperienceTranslationCreate,
  FieldValidationData
> = {
  language: {
    label: "Language",
    validation: Yup.string(),
  },
  title: {
    label: "Title",
    validation: Yup.string(),
  },
  description: {
    label: "Description",
    validation: Yup.string(),
  },
  accept_button_label: {
    label: "Accept button label",
    validation: Yup.string(),
  },
  reject_button_label: {
    label: "Reject button label",
    validation: Yup.string(),
  },
  save_button_label: {
    label: "Save button label",
    validation: Yup.string(),
  },
  acknowledge_button_label: {
    label: "Acknowledge button label",
    validation: Yup.string(),
  },
  privacy_policy_url: {
    label: "Privacy policy URL",
    validation: Yup.string().url(),
  },
  privacy_preferences_link_label: {
    label: "Privacy preferences link label",
    validation: Yup.string(),
  },
  banner_title: {
    label: "Banner title",
    validation: Yup.string(),
  },
  banner_description: {
    label: "Banner description",
    validation: Yup.string(),
  },
  purpose_header: {
    label: "Purpose header",
    validation: Yup.string(),
  },
  privacy_policy_link_label: {
    label: "Privacy policy link label",
    validation: Yup.string(),
  },
  modal_link_label: {
    label: "Modal link label",
    validation: Yup.string(),
  },
  is_default: {
    label: "Default language",
    validation: Yup.boolean(),
  },
};
