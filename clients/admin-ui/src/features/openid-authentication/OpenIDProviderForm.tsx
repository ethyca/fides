import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import {
  Box,
  Button,
  ConfirmationModal,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useCreateOpenIDProviderMutation,
  useDeleteOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
} from "~/features/openid-authentication/openprovider.slice";
import { OpenIDProvider } from "~/types/api";

interface OpenIDProviderFormProps {
  openIDProvider?: OpenIDProvider;
  onSuccess?: (openIDProvider: OpenIDProvider) => void;
}

export interface OpenIDProviderFormValues extends OpenIDProvider {}

export const defaultInitialValues: OpenIDProviderFormValues = {
  id: "",
  provider: "",
  client_id: "",
  client_secret: "",
};

export const transformOrganizationToFormValues = (
  openIDProvider: OpenIDProvider
): OpenIDProviderFormValues => ({ ...openIDProvider });

export const transformFormValuesToOpenIDProvider = (
  formValues: OpenIDProviderFormValues
): OpenIDProvider => ({
  id: formValues.id,
  provider: formValues.provider,
  client_id: formValues.client_id,
  client_secret: formValues.client_secret,
});

const OpenIDProviderFormValidationSchema = Yup.object().shape({
  provider: Yup.string().required().label("Provider"),
  client_id: Yup.string().required().label("Client ID"),
  client_secret: Yup.string().required().label("Client Secret"),
});

export const OpenIDProviderForm = ({
  openIDProvider,
  onSuccess,
}: OpenIDProviderFormProps) => {
  const [createOpenIDProviderMutationTrigger] =
    useCreateOpenIDProviderMutation();
  const [updateOpenIDProviderMutation, updateOpenIDProviderMutationResult] =
    useUpdateOpenIDProviderMutation();
  const [deleteOpenIDProviderMutation] = useDeleteOpenIDProviderMutation();

  const initialValues = useMemo(
    () =>
      openIDProvider
        ? transformOrganizationToFormValues(openIDProvider)
        : defaultInitialValues,
    [openIDProvider]
  );

  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const toast = useToast();

  const handleSubmit = async (
    values: OpenIDProviderFormValues,
    formikHelpers: FormikHelpers<OpenIDProviderFormValues>
  ) => {
    const openIDProviderBody = transformFormValuesToOpenIDProvider(values);

    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the OpenID Provider. Please try again."
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("OpenID Provider configuration saved."));
        formikHelpers.resetForm({});
        if (onSuccess) {
          onSuccess(openIDProviderBody);
        }
      }
    };
    if (initialValues.id) {
      const result = await updateOpenIDProviderMutation(openIDProviderBody);
      handleResult(result);
    } else {
      const result = await createOpenIDProviderMutationTrigger(
        openIDProviderBody
      );
      handleResult(result);
    }
  };

  const handleDelete = async () => {
    const result = await deleteOpenIDProviderMutation(
      initialValues.id as string
    );

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      onDeleteClose();
      return;
    }

    toast(successToastParams(`OpenID Provider deleted successfully`));

    onDeleteClose();
  };

  const PROVIDER_OPTIONS = [{ label: "Google", value: "google" }];

  // Show the loading state if the openIDProvider is null or being updated
  let isLoading =
    !openIDProvider || updateOpenIDProviderMutationResult.isLoading;
  isLoading = false;
  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={OpenIDProviderFormValidationSchema}
    >
      {({ dirty, isValid }) => (
        <Form data-testid="openIDProvider-form">
          <Stack spacing={4}>
            <CustomSelect
              name="provider"
              label="Provider"
              options={PROVIDER_OPTIONS}
              variant="stacked"
              isRequired
            />
            <CustomTextInput
              id="client_id"
              name="client_id"
              label="Client ID"
              disabled={isLoading}
              tooltip="Client ID for your provider"
              variant="stacked"
              isRequired
            />
            <CustomTextInput
              id="client_secret"
              name="client_secret"
              label="Client Secret"
              disabled={isLoading}
              tooltip="Client Secret for your provider"
              variant="stacked"
              isRequired
            />
            <Box textAlign="right">
              {initialValues.id && true && (
                <Button
                  data-testid="delete-template-button"
                  size="sm"
                  variant="outline"
                  isLoading={false}
                  mr={3}
                  onClick={onDeleteOpen}
                >
                  Delete
                </Button>
              )}
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isDisabled={isLoading || !dirty || !isValid}
                isLoading={isLoading}
                data-testid="save-btn"
              >
                Save
              </Button>
            </Box>
          </Stack>
          <ConfirmationModal
            isOpen={deleteIsOpen}
            onClose={onDeleteClose}
            onConfirm={handleDelete}
            title="Delete OpenID provider"
            message={
              <Text>
                You are about to permanently delete this OpenID provider. Are
                you sure you would like to continue?
              </Text>
            }
          />
        </Form>
      )}
    </Formik>
  );
};
