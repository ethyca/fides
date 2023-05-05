import FormSection from "~/features/common/form/FormSection";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";

import { ExperienceFormRules } from "./helpers";

/**
 * Banner text form component.
 * Rules:
 *   * Only renders on component_type = OVERLAY
 */
const BannerTextForm = ({ isOverlay }: ExperienceFormRules) => {
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
