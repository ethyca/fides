import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";

const PrivacyPolicy = () => (
  <FormSection
    title="Privacy policy link configuration"
    data-testid="privacy-policy"
  >
    <CustomTextInput
      name="privacy_policy_link_label"
      label="Privacy policy link label"
      variant="stacked"
    />
    <CustomTextInput
      name="privacy_policy_url"
      label="Privacy policy URL"
      variant="stacked"
    />
  </FormSection>
);

export default PrivacyPolicy;
