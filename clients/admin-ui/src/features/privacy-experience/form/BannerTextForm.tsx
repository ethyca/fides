import { useFormikContext } from "formik";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { PrivacyExperienceCreate } from "~/types/api";

import { useExperienceFormRules } from "./helpers";

/**
 * Banner text form component.
 * Rules:
 *   * Only renders on component_type = OVERLAY
 */
const BannerTextForm = () => {
  const { initialValues } = useFormikContext<PrivacyExperienceCreate>();
  const { isOverlay } = useExperienceFormRules({
    privacyExperience: initialValues,
  });

  if (!isOverlay) {
    return null;
  }

  return (
    <FormSection title="Banner text" data-testid="banner-text-form">
      <CustomTextInput
        name="banner_title"
        label="Banner title"
        variant="stacked"
        isRequired
      />
      <CustomTextArea
        label="Banner description"
        name="banner_description"
        variant="stacked"
      />
    </FormSection>
  );
};

export default BannerTextForm;
