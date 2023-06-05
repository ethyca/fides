import { useMemo } from "react";
import * as Yup from "yup";

import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceConfigResponse,
  PrivacyNoticeResponse,
} from "~/types/api";

export const defaultInitialValues: ExperienceConfigCreate = {
  title: "",
  description: "",
  accept_button_label: "",
  reject_button_label: "",
  save_button_label: "",
  regions: [],
  component: ComponentType.OVERLAY,
};

export const transformExperienceConfigResponseToCreation = (
  experienceConfig: ExperienceConfigResponse
): ExperienceConfigCreate => {
  // Remove the fields not needed for editing/creation
  const {
    created_at: createdAt,
    updated_at: updatedAt,
    version,
    experience_config_history_id: experienceConfigHistoryId,
    ...rest
  } = experienceConfig;
  return {
    ...rest,
    title: experienceConfig.title ?? "",
    description: experienceConfig.description ?? "",
    accept_button_label: experienceConfig.accept_button_label ?? "",
    reject_button_label: experienceConfig.reject_button_label ?? "",
    save_button_label: experienceConfig.save_button_label ?? "",
    regions: experienceConfig.regions ?? defaultInitialValues.regions,
    component: experienceConfig.component ?? defaultInitialValues.component,
  };
};

const buttonGroupValidationSchema = Yup.object().shape({
  accept_button_label: Yup.string().label("Accept button label").required(),
  reject_button_label: Yup.string().required().label("Reject button label"),
  save_button_label: Yup.string().required().label("Save button label"),
});

const privacyCenterValidationSchema = Yup.object()
  .shape({
    title: Yup.string().required().label("Title"),
    description: Yup.string().required().label("Description"),
  })
  .concat(buttonGroupValidationSchema);

const bannerValidationSchema = Yup.object()
  .shape({
    title: Yup.string().required().label("Banner title"),
    description: Yup.string().required().label("Banner description"),
    acknowledge_button_label: Yup.string()
      .required()
      .label("Acknowledge button label"),
    privacy_preferences_link_label: Yup.string()
      .required()
      .label("Privacy preferences link label"),
  })
  .concat(buttonGroupValidationSchema);

/**
 * Use the various rules/conditions of a privacy experience form
 */
export const useExperienceForm = ({
  privacyExperience,
}: {
  privacyExperience: ExperienceConfigCreate;
  privacyNotices?: PrivacyNoticeResponse[];
}) => {
  const isOverlay = useMemo(
    () => privacyExperience.component === ComponentType.OVERLAY,
    [privacyExperience.component]
  );

  // Build the validation schema based on the rules
  const validationSchema = useMemo(() => {
    if (!isOverlay) {
      return privacyCenterValidationSchema;
    }
    return bannerValidationSchema;
  }, [isOverlay]);

  return {
    isOverlay,
    validationSchema,
  };
};
