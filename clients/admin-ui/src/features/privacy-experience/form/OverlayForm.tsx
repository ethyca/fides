import { Stack } from "@fidesui/react";

import FormSection from "~/features/common/form/FormSection";
import {
  CustomSelect,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { BANNER_ENABLED_MAP } from "~/features/privacy-experience/constants";
import { BannerEnabled } from "~/types/api";

import PrivacyPolicy from "./PrivacyPolicy";

const BANNER_ENABLED_OPTIONS = enumToOptions(BannerEnabled).map((opt) => ({
  ...opt,
  label: BANNER_ENABLED_MAP.get(opt.value) ?? opt.label,
}));

const OverlayForm = () => (
  <Stack spacing={6}>
    <FormSection
      title="Overlay & banner configuration"
      data-testid="banner-and-preferences-labeling"
    >
      <CustomTextInput
        label="Title, displayed on both the overlay and banner"
        name="title"
        variant="stacked"
        isRequired
      />
      <CustomTextArea
        label="Description, displayed on both the overlay and banner"
        name="description"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Banner title, if different from overlay"
        name="banner_title"
        variant="stacked"
      />
      <CustomTextArea
        label="Banner description, if different from overlay"
        name="banner_description"
        variant="stacked"
      />
      <CustomTextInput
        label="“Accept” button label, displayed on both the overlay and banner"
        name="accept_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="“Reject” button label, displayed on both the overlay and banner"
        name="reject_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="“Manage preferences” button label, displayed only on the banner"
        name="privacy_preferences_link_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="“Save” button label, displayed only on the overlay"
        name="save_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="“Acknowledge” button label, displayed only on a notice-only banner"
        name="acknowledge_button_label"
        variant="stacked"
        isRequired
      />
    </FormSection>
    <PrivacyPolicy />
    <FormSection
      title="Display configuration"
      data-testid="display-configuration"
    >
      <CustomSelect
        name="banner_enabled"
        label="Banner"
        options={BANNER_ENABLED_OPTIONS}
        variant="stacked"
        isRequired
      />
    </FormSection>
  </Stack>
);

export default OverlayForm;
