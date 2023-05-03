import { useFormikContext } from "formik";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";
import {
  ComponentType,
  ConsentMechanism,
  PrivacyExperienceCreate,
  PrivacyNoticeResponse,
} from "~/types/api";

/**
 * Banner text form component.
 * Rules:
 *   * Only renders on component_type = OVERLAY
 *   * If the experience only has notice_only notices, renders an "Acknowledgment button" instead of confirm + reject
 */
const BannerActionForm = ({
  privacyNotices,
}: {
  privacyNotices?: PrivacyNoticeResponse[];
}) => {
  const { initialValues } = useFormikContext<PrivacyExperienceCreate>();

  if (initialValues.component === ComponentType.PRIVACY_CENTER) {
    return null;
  }

  // Special rules for if the banner _only_ has notice only notices
  if (
    privacyNotices &&
    privacyNotices.length &&
    privacyNotices.every(
      (notice) => notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
    )
  ) {
    return (
      <FormSection title="Banner actions">
        <CustomTextInput
          name="link_label"
          label="Link label"
          variant="stacked"
        />
        <CustomTextInput
          label="Acknowledgment button label"
          name="acknowledgement_button_label"
          variant="stacked"
        />
      </FormSection>
    );
  }

  return (
    <FormSection title="Banner actions">
      <CustomTextInput name="link_label" label="Link label" variant="stacked" />
      <CustomTextInput
        label="Confirmation button label"
        name="confirmation_button_label"
        variant="stacked"
      />
      <CustomTextInput
        label="Reject button label"
        name="reject_button_label"
        variant="stacked"
      />
    </FormSection>
  );
};

export default BannerActionForm;
