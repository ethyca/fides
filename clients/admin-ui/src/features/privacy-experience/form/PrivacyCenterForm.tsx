import { Stack } from "@fidesui/react";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";

import PrivacyPolicy from "./PrivacyPolicy";

const PrivacyCenterForm = () => (
  <Stack spacing={6}>
    <FormSection title="Consent page text" data-testid="consent-page-text">
      <CustomTextInput
        name="title"
        label="Title"
        variant="stacked"
        isRequired
      />
      <CustomTextArea
        label="Description"
        name="description"
        variant="stacked"
      />
    </FormSection>
    <FormSection title="Actions" data-testid="actions">
      <CustomTextInput
        label="Save button label"
        name="save_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Reject button label"
        name="reject_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Accept button label"
        name="accept_button_label"
        variant="stacked"
        isRequired
      />
    </FormSection>
    <PrivacyPolicy />
  </Stack>
);

export default PrivacyCenterForm;
