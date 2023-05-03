import { useFormikContext } from "formik";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";
import { ComponentType, PrivacyExperienceCreate } from "~/types/api";

/**
 * Privacy center configuration form
 * Rules:
 *   * Only renders on component_type = privacy_center
 */
const PrivacyCenterMessagingForm = () => {
  const { initialValues } = useFormikContext<PrivacyExperienceCreate>();

  if (initialValues.component === ComponentType.OVERLAY) {
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
