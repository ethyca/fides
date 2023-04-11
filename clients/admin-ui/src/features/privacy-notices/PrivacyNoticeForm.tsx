import { Button, ButtonGroup, Stack } from "@fidesui/react";

import { PrivacyNoticeResponse } from "~/types/api";

import FormSection from "../common/form/FormSection";
import {
  defaultInitialValues,
  transformPrivacyNoticeResponseToCreation,
} from "./form";

const PrivacyNoticeForm = ({
  privacyNotice: passedInPrivacyNotice,
}: {
  privacyNotice?: PrivacyNoticeResponse;
}) => {
  const initialValues = passedInPrivacyNotice
    ? transformPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
    : defaultInitialValues;

  return (
    <Stack spacing={10}>
      <Stack spacing={6}>
        <FormSection title="Privacy notice information">
          {initialValues.name}
        </FormSection>
        <FormSection title="Consent mechanism">
          {initialValues.consent_mechanism}
        </FormSection>
        <FormSection title="Privacy notice configuration">
          {initialValues.data_uses}
        </FormSection>
      </Stack>
      <ButtonGroup size="sm" spacing={4}>
        <Button variant="outline">Cancel</Button>
        <Button colorScheme="primary">Save</Button>
      </ButtonGroup>
    </Stack>
  );
};

export default PrivacyNoticeForm;
