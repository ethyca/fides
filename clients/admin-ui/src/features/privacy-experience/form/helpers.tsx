import { useMemo } from "react";
import * as Yup from "yup";

import {
  ComponentType,
  ConsentMechanism,
  DeliveryMechanism,
  PrivacyExperienceCreate,
  PrivacyExperienceResponse,
  PrivacyNoticeResponse,
} from "~/types/api";

export const defaultInitialValues: PrivacyExperienceCreate = {
  regions: [],
  component: ComponentType.OVERLAY,
  delivery_mechanism: DeliveryMechanism.LINK,
};

export const transformPrivacyExperienceResponseToCreation = (
  experience: PrivacyExperienceResponse
): PrivacyExperienceCreate => {
  // Remove the fields not needed for editing/creation
  const {
    created_at: createdAt,
    updated_at: updatedAt,
    privacy_experience_history_id: historyId,
    privacy_experience_template_id: templateId,
    version,
    privacy_notices: notices,
    ...rest
  } = experience;
  return {
    ...rest,

    regions: experience.regions ?? defaultInitialValues.regions,
    component: experience.component ?? defaultInitialValues.component,
    delivery_mechanism:
      experience.delivery_mechanism ?? defaultInitialValues.delivery_mechanism,
  };
};

const privacyCenterValidationSchema = Yup.object().shape({
  link_label: Yup.string().required().label("Link label"),
  component_description: Yup.string(),
});

const bannerValidationSchema = Yup.object().shape({
  banner_title: Yup.string().required().label("Banner title"),
  banner_description: Yup.string(),
  link_label: Yup.string().required().label("Link label"),
});

const confirmRejectValidationSchema = Yup.object().shape({
  confirmation_button_label: Yup.string()
    .required()
    .label("Confirmation button label"),
  reject_button_label: Yup.string().required().label("Reject button label"),
});

const acknowledgeValidationSchema = Yup.object().shape({
  acknowledgement_button_label: Yup.string()
    .required()
    .label("Acknowledgment button label"),
});

/**
 * Use the various rules/conditions of a privacy experience form
 */
export const useExperienceFormRules = ({
  privacyExperience,
  privacyNotices,
}: {
  privacyExperience: PrivacyExperienceCreate;
  privacyNotices?: PrivacyNoticeResponse[];
}) => {
  const isOverlay = useMemo(
    () => privacyExperience.component === ComponentType.OVERLAY,
    [privacyExperience.component]
  );

  const needsBanner = useMemo(
    () =>
      privacyNotices &&
      privacyNotices.some(
        (notice) =>
          notice.consent_mechanism === ConsentMechanism.OPT_IN ||
          notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
      ),
    [privacyNotices]
  );

  const hasOnlyNoticeOnlyNotices = useMemo(
    () =>
      privacyNotices &&
      privacyNotices.length &&
      privacyNotices.every(
        (notice) => notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
      ),
    [privacyNotices]
  );

  // Build the validation schema based on the rules
  const validationSchema = useMemo(() => {
    if (!isOverlay) {
      return privacyCenterValidationSchema;
    }

    const buttonSchema = hasOnlyNoticeOnlyNotices
      ? acknowledgeValidationSchema
      : confirmRejectValidationSchema;
    return bannerValidationSchema.concat(buttonSchema);
  }, [isOverlay, hasOnlyNoticeOnlyNotices]);

  return {
    isOverlay,
    needsBanner,
    hasOnlyNoticeOnlyNotices,
    validationSchema,
  };
};
