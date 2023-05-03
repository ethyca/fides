import { Box, Button, ButtonGroup, Stack, Tag, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import FormSection from "~/features/common/form/FormSection";
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

import BannerActionForm from "./BannerActionForm";
import BannerTextForm from "./BannerTextForm";
import DeliveryMechanismForm from "./DeliveryMechanismForm";
import {
  defaultInitialValues,
  transformPrivacyExperienceResponseToCreation,
  ValidationSchema,
} from "./helpers";
import PrivacyCenterMessagingForm from "./PrivacyCenterMessagingForm";

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

  const associatedNotices = passedInPrivacyExperience
    ? passedInPrivacyExperience.privacy_notices
    : undefined;

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form>
          <pre>
            notice mechanisms:{" "}
            {associatedNotices?.map((n) => `${n.consent_mechanism}, `)}
          </pre>
          <Stack spacing={10}>
            <Stack spacing={6}>
              {/* Location shows in every form */}
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
              {/* Form subsections are responsible for their own render/don't render logic */}
              <DeliveryMechanismForm privacyNotices={associatedNotices} />
              <PrivacyCenterMessagingForm />
              <BannerTextForm />
              <BannerActionForm privacyNotices={associatedNotices} />
              {/* End form subsections */}
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
