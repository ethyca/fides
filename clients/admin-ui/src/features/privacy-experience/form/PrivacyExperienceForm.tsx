import { Box, Button, ButtonGroup, Stack, Tag, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  usePatchPrivacyExperienceMutation,
  usePostPrivacyExperienceMutation,
} from "~/features/privacy-experience/privacy-experience.slice";
import {
  PrivacyExperienceCreate,
  PrivacyExperienceResponse,
} from "~/types/api";

import {
  defaultInitialValues,
  transformPrivacyExperienceResponseToCreation,
  ValidationSchema,
} from "./helpers";

const PrivacyNoticeForm = ({
  privacyExperience: passedInPrivacyExperience,
}: {
  privacyExperience?: PrivacyExperienceResponse;
}) => {
  const router = useRouter();
  const toast = useToast();
  const initialValues = passedInPrivacyExperience
    ? transformPrivacyExperienceResponseToCreation(passedInPrivacyExperience)
    : defaultInitialValues;

  const [patchExperiencesMutationTrigger] = usePatchPrivacyExperienceMutation();
  const [postExperiencesMutationTrigger] = usePostPrivacyExperienceMutation();

  const isEditing = useMemo(
    () => !!passedInPrivacyExperience,
    [passedInPrivacyExperience]
  );

  const handleSubmit = async (values: PrivacyExperienceCreate) => {
    let result;
    if (isEditing) {
      result = await patchExperiencesMutationTrigger([values]);
    } else {
      result = await postExperiencesMutationTrigger([values]);
    }

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Privacy experience ${isEditing ? "updated" : "created"}`
        )
      );
      if (!isEditing) {
        router.push(PRIVACY_EXPERIENCE_ROUTE);
      }
    }
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
              <FormSection title="Locations">
                <Box
                  border="1px solid"
                  borderColor="gray.200"
                  borderRadius="md"
                  p={5}
                  m={0}
                >
                  {initialValues.regions.map((r) => (
                    <Tag
                      key={r}
                      mr="2"
                      backgroundColor="primary.400"
                      color="white"
                    >
                      {r}
                    </Tag>
                  ))}
                </Box>
              </FormSection>
              <FormSection title="Banner text">
                <CustomTextInput
                  name="banner_title"
                  label="Banner title"
                  variant="stacked"
                />
                <CustomTextArea
                  label="Banner description"
                  name="banner_description"
                  variant="stacked"
                />
              </FormSection>
              <FormSection title="Banner actions">
                <CustomTextInput
                  name="link_label"
                  label="Link label"
                  variant="stacked"
                />
                <CustomTextInput
                  label="Confirmation button label"
                  name="confirmation_button_label"
                  variant="stacked"
                />
                <CustomTextInput
                  label="Reject button label"
                  name="reject_button_label"
                  variant="stacked"
                />
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
