import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { AntButton, Box, Stack, useToast } from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useUpdateOrganizationMutation,
} from "~/features/organization";
import { Organization } from "~/types/api";

// NOTE: This form only supports *editing* Organizations right now, and
// does not support creation/deletion. Since Fides will automatically create the
// "default_organization" on startup, this works!
//
// However, note that if the provided `organization` prop is null, the form
// will still render but all fields will be disabled and it will display as
// "loading". This allows the form to render immediately while the parent
// fetches the Organization via the API
interface OrganizationFormProps {
  organization?: Organization;
  onSuccess?: (organization: Organization) => void;
}

export interface OrganizationFormValues extends Organization {}

export const defaultInitialValues: OrganizationFormValues = {
  description: "",
  fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
  name: "",
};

// NOTE: These transform functions are (basically) unnecessary right now, since
// the form values are an exact match to the Organization object. However, in
// future iterations some transformation is likely to be necessary, so we've
// put these transform functions in place ahead of time to make future updates
// easier to make
export const transformOrganizationToFormValues = (
  organization: Organization,
): OrganizationFormValues => ({ ...organization });

export const transformFormValuesToOrganization = (
  formValues: OrganizationFormValues,
): Organization => ({
  description: formValues.description,
  fides_key: formValues.fides_key,
  name: formValues.name,
});

const OrganizationFormValidationSchema = Yup.object().shape({
  description: Yup.string().required().label("Description"),
  fides_key: Yup.string().required().label("Organization Fides Key"),
  name: Yup.string().required().label("Name"),
});

export const OrganizationForm = ({
  organization,
  onSuccess,
}: OrganizationFormProps) => {
  const [updateOrganizationMutation, updateOrganizationMutationResult] =
    useUpdateOrganizationMutation();

  const initialValues = useMemo(
    () =>
      organization
        ? transformOrganizationToFormValues(organization)
        : defaultInitialValues,
    [organization],
  );

  const toast = useToast();

  const handleSubmit = async (
    values: OrganizationFormValues,
    formikHelpers: FormikHelpers<OrganizationFormValues>,
  ) => {
    const organizationBody = transformFormValuesToOrganization(values);

    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the organization. Please try again.",
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Organization configuration saved."));
        // TODO: is this needed? Copied from SystemInformationForm which is more complex
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
        if (onSuccess) {
          onSuccess(organizationBody);
        }
      }
    };

    const result = await updateOrganizationMutation(organizationBody);
    handleResult(result);
  };

  // Show the loading state if the organization is null or being updated
  const isLoading = !organization || updateOrganizationMutationResult.isLoading;
  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={OrganizationFormValidationSchema}
    >
      {({ dirty, isValid }) => (
        <Form data-testid="organization-form">
          <Stack spacing={4}>
            <CustomTextInput
              id="fides_key"
              name="fides_key"
              label="Fides Key"
              disabled
              tooltip="A unique key that identifies your organization. Not editable via UI."
              variant="stacked"
            />
            <CustomTextInput
              id="name"
              name="name"
              label="Name"
              disabled={isLoading}
              tooltip="User-friendly name for your organization, used in messaging to end-users and other public locations."
              variant="stacked"
            />
            <CustomTextInput
              id="description"
              name="description"
              label="Description"
              disabled={isLoading}
              tooltip="Short description of your organization, your services, etc."
              variant="stacked"
            />
            <Box textAlign="right">
              <AntButton
                htmlType="submit"
                type="primary"
                disabled={isLoading || !dirty || !isValid}
                loading={isLoading}
                data-testid="save-btn"
              >
                Save
              </AntButton>
            </Box>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
