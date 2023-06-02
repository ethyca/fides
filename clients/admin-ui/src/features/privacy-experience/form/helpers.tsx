import { useMemo } from "react";
import * as Yup from "yup";

import {
  ComponentType,
  DeliveryMechanism,
  ExperienceConfigCreate,
  ExperienceConfigResponse,
  PrivacyNoticeResponse,
} from "~/types/api";

export const defaultInitialValues: ExperienceConfigCreate = {
  component_title: "",
  regions: [],
  component: ComponentType.OVERLAY,
  delivery_mechanism: DeliveryMechanism.LINK,
};

export const transformExperienceConfigResponseToCreation = (
  experienceConfig: ExperienceConfigResponse
): ExperienceConfigCreate => {
  // Remove the fields not needed for editing/creation
  const {
    created_at: createdAt,
    updated_at: updatedAt,
    ...rest
  } = experienceConfig;
  return {
    ...rest,
    component_title: experienceConfig.component_title ?? "",
    regions: experienceConfig.regions ?? defaultInitialValues.regions,
    component: experienceConfig.component ?? defaultInitialValues.component,
    delivery_mechanism:
      experienceConfig.delivery_mechanism ??
      defaultInitialValues.delivery_mechanism,
  };
};

const privacyCenterValidationSchema = Yup.object().shape({
  link_label: Yup.string().required().label("Link label"),
  component_description: Yup.string().nullable(),
});

const bannerValidationSchema = Yup.object().shape({
  banner_title: Yup.string().required().label("Banner title"),
  banner_description: Yup.string().nullable(),
  link_label: Yup.string().label("Link label").nullable(),
});

const buttonGroupValidationSchema = Yup.object().shape({
  acknowledgement_button_label: Yup.string()
    .required()
    .label("Acknowledgment button label"),
  confirmation_button_label: Yup.string()
    .required()
    .label("Confirmation button label"),
  reject_button_label: Yup.string().required().label("Reject button label"),
});

export interface ExperienceFormRules {
  isOverlay: boolean;
}

/**
 * Use the various rules/conditions of a privacy experience form
 */
export const useExperienceFormRules = ({
  privacyExperience,
}: {
  privacyExperience: ExperienceConfigCreate;
  privacyNotices?: PrivacyNoticeResponse[];
}): ExperienceFormRules & { validationSchema: any } => {
  const isOverlay = useMemo(
    () => privacyExperience.component === ComponentType.OVERLAY,
    [privacyExperience.component]
  );

  // Build the validation schema based on the rules
  const validationSchema = useMemo(() => {
    if (!isOverlay) {
      return privacyCenterValidationSchema;
    }
    return bannerValidationSchema.concat(buttonGroupValidationSchema);
  }, [isOverlay]);

  return {
    isOverlay,
    validationSchema,
  };
};
