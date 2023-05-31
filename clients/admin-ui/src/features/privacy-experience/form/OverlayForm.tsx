import { Stack } from "@fidesui/react";

import FormSection from "~/features/common/form/FormSection";
import {
  CustomSelect,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import InfoBox from "~/features/common/InfoBox";
import { BANNER_ENABLED_MAP } from "~/features/privacy-experience/constants";
import { BannerEnabled } from "~/types/api";

import PrivacyPolicy from "./PrivacyPolicy";

const BANNER_ENABLED_OPTIONS = enumToOptions(BannerEnabled).map((opt) => ({
  ...opt,
  label: BANNER_ENABLED_MAP.get(opt.value) ?? opt.label,
}));

const INFO_TEXT =
  "Configure your notice only banner, your consent banner and your privacy preferences below. It is good practice to complete all fields regardless of whether you are showing a notice only banner or an opt-in/opt-out banner.";

const OverlayForm = () => (
  <Stack spacing={6}>
    <InfoBox text={INFO_TEXT} />
    <FormSection
      title="Cookie banner and privacy preferences labeling"
      data-testid="banner-and-preferences-labeling"
    >
      <CustomTextInput
        name="title"
        label="Banner title"
        variant="stacked"
        isRequired
      />
      <CustomTextArea
        label="Banner description"
        name="description"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Accept button displayed on the Banner and “Privacy preferences”"
        name="accept_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Reject button displayed on the Banner and “Privacy preferences”"
        name="reject_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="“Privacy preferences” link label"
        name="privacy_preferences_link_label"
        variant="stacked"
      />
      <CustomTextInput
        label="Privacy preferences “Save” button label"
        name="save_button_label"
        variant="stacked"
        isRequired
      />
      <CustomTextInput
        label="Acknowledge button label for notice only banner"
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
