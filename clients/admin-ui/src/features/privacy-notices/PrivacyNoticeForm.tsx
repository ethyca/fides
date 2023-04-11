import { Button, ButtonGroup, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";

import FormSection from "~/features/common/form/FormSection";
import { PrivacyNoticeCreation, PrivacyNoticeResponse } from "~/types/api";

import {
  defaultInitialValues,
  transformPrivacyNoticeResponseToCreation,
  ValidationSchema,
} from "./form";

const PrivacyNoticeForm = ({
  privacyNotice: passedInPrivacyNotice,
}: {
  privacyNotice?: PrivacyNoticeResponse;
}) => {
  const router = useRouter();
  const initialValues = passedInPrivacyNotice
    ? transformPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
    : defaultInitialValues;

  const handleSubmit = (values: PrivacyNoticeCreation) => {
    console.log({ values });
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form>
          <Stack spacing={10}>
            <Stack spacing={6}>
              <FormSection title="Privacy notice details">
                {initialValues.name}
              </FormSection>
              <FormSection title="Consent mechanism">
                {initialValues.consent_mechanism}
              </FormSection>
              <FormSection title="Privacy notice configuration">
                {initialValues.data_uses}
              </FormSection>
            </Stack>
            <ButtonGroup size="sm" spacing={2}>
              <Button
                variant="outline"
                onClick={() => {
                  router.back();
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isDisabled={isSubmitting || !dirty || !isValid}
                isLoading={isSubmitting}
                data-testid="save-btn"
              >
                Save
              </Button>
            </ButtonGroup>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PrivacyNoticeForm;
