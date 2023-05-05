import { useFormikContext } from "formik";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";
import { PrivacyExperienceCreate } from "~/types/api";

import { useExperienceFormRules } from "./helpers";

/**
 * Privacy center configuration form
 * Rules:
 *   * Only renders on component_type = privacy_center
 */
const PrivacyCenterMessagingForm = () => {
  const { initialValues } = useFormikContext<PrivacyExperienceCreate>();

  const { isOverlay } = useExperienceFormRules({
    privacyExperience: initialValues,
  });

  if (isOverlay) {
    return null;
  }

  return (
    <FormSection
      title="Privacy center messaging"
      data-testid="privacy-center-messaging-form"
    >
      <CustomTextInput
        name="link_label"
        label="Website link text"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        name="component_description"
        label="Privacy center heading text"
        variant="stacked"
      />
    </FormSection>
  );
};

export default PrivacyCenterMessagingForm;
