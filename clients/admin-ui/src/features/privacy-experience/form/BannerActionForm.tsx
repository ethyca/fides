import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";

import { ExperienceFormRules } from "./helpers";

/**
 * Banner text form component.
 * Rules:
 *   * Only renders on component_type = OVERLAY
 */
const BannerActionForm = ({ isOverlay }: ExperienceFormRules) => {
  if (!isOverlay) {
    return null;
  }

  return (
    <FormSection title="Banner actions" data-testid="banner-action-form">
      <CustomTextInput name="link_label" label="Link label" variant="stacked" />
      <CustomTextInput
        label="Acknowledgment button label"
        name="acknowledgement_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Confirmation button label"
        name="confirmation_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Reject button label"
        name="reject_button_label"
        variant="stacked"
        isRequired
      />
    </FormSection>
  );
};

export default BannerActionForm;
