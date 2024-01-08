import { Button, ButtonGroup, Stack, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  usePatchExperienceConfigMutation,
  usePostExperienceConfigMutation,
} from "~/features/privacy-experience/privacy-experience.slice";
import { ExperienceConfigCreate, ExperienceConfigResponse } from "~/types/api";

import {
  defaultInitialValues,
  transformExperienceConfigResponseToCreation,
  transformFormValuesToExperienceConfigCreate,
  transformFormValuesToExperienceConfigUpdate,
  useExperienceForm,
} from "./helpers";
import OverlayForm from "./OverlayForm";
import PrivacyCenterForm from "./PrivacyCenterForm";

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
      // Cannot change component (BE will not accept it)
      const { component, ...payload } = values;
      result = await patchExperiencesMutationTrigger(
        transformFormValuesToExperienceConfigUpdate({
          ...payload,
          id: passedInPrivacyExperience.id,
        })
      );
    } else {
      result = await postExperiencesMutationTrigger(
        transformFormValuesToExperienceConfigCreate(values)
      );
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

  const { validationSchema, isOverlay } = useExperienceForm({
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
            {isOverlay ? <OverlayForm /> : <PrivacyCenterForm />}
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
