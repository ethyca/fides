import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";

import { ExperienceFormRules } from "./helpers";

/**
 * Privacy center configuration form
 * Rules:
 *   * Only renders on component_type = privacy_center
 */
const PrivacyCenterMessagingForm = ({ isOverlay }: ExperienceFormRules) => {
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
