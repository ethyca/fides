import { Box, Button, ButtonGroup, Stack, Tag, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import FormSection from "~/features/common/form/FormSection";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  usePatchExperienceConfigMutation,
  usePostExperienceConfigMutation,
} from "~/features/privacy-experience/privacy-experience.slice";
import { ExperienceConfigCreate, ExperienceConfigResponse } from "~/types/api";

import BannerActionForm from "./BannerActionForm";
import BannerTextForm from "./BannerTextForm";
import DeliveryMechanismForm from "./DeliveryMechanismForm";
import {
  defaultInitialValues,
  transformExperienceConfigResponseToCreation,
  useExperienceFormRules,
} from "./helpers";
import PrivacyCenterMessagingForm from "./PrivacyCenterMessagingForm";

const PrivacyExperienceForm = ({
  privacyExperience: passedInPrivacyExperience,
}: {
  privacyExperience?: ExperienceConfigResponse;
}) => {
  const router = useRouter();
  const toast = useToast();
  const initialValues = passedInPrivacyExperience
    ? transformExperienceConfigResponseToCreation(passedInPrivacyExperience)
    : defaultInitialValues;

  const [patchExperiencesMutationTrigger] = usePatchExperienceConfigMutation();
  const [postExperiencesMutationTrigger] = usePostExperienceConfigMutation();

  const isEditing = useMemo(
    () => !!passedInPrivacyExperience,
    [passedInPrivacyExperience]
  );

  const handleSubmit = async (values: ExperienceConfigCreate) => {
    let result;
    if (isEditing && passedInPrivacyExperience) {
      result = await patchExperiencesMutationTrigger({
        ...values,
        id: passedInPrivacyExperience.id,
      });
    } else {
      result = await postExperiencesMutationTrigger(values);
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

  const { validationSchema, ...rules } = useExperienceFormRules({
    privacyExperience: initialValues,
  });

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={validationSchema}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form>
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
              <DeliveryMechanismForm {...rules} />
              <PrivacyCenterMessagingForm {...rules} />
              <BannerTextForm {...rules} />
              <BannerActionForm {...rules} />
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

export default PrivacyExperienceForm;
